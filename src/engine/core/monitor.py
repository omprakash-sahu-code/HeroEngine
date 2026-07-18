import time
import threading
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple, Any

from src.engine.utils.logger import setup_logger
from src.engine.core.profiler_types import ProfileSection, ProfileSnapshot
from src.engine.core.system_metrics import SystemMetricsProvider, create_system_metrics_provider

logger = setup_logger("Monitor")

class ProfileContext:
    """Exception-safe context manager for section timing."""

    def __init__(self, monitor: "PerformanceMonitor", section_name: str):
        self.monitor = monitor
        self.section_name = section_name
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        self.monitor.record_latency(self.section_name, duration_ms)
        # Do not suppress exceptions
        return False


class PerformanceMonitor:
    """Thread-safe performance monitoring and profiling system maintaining bounded rolling

    window histories (300 frames), percentiles, and system load sampling.
    """

    def __init__(
        self,
        window_size: int = 300,
        system_provider: Optional[SystemMetricsProvider] = None
    ):
        """Args:

            window_size: Maximum number of frames to retain in rolling window deques (~5 seconds at 60 FPS).
            system_provider: Hardware resource metrics provider for CPU/RAM sampling.
        """
        self.window_size = window_size
        self.system_provider = system_provider or create_system_metrics_provider()
        
        self._lock = threading.Lock()
        self._frame_times: deque = deque(maxlen=window_size)
        self._last_tick_time = time.perf_counter()
        
        self._section_latencies: Dict[str, deque] = {}
        self._timers: Dict[str, float] = {}
        
        self.frame_counter = 0
        self.fps = 0.0
        self.display_enabled = False  # Controlled via F3 toggle

    def tick(self) -> float:
        """Call at the start of each frame tick to update FPS metrics.

        Returns:
            float: Elapsed time since last tick in seconds (dt).
        """
        current_time = time.perf_counter()
        dt = max(1e-6, current_time - self._last_tick_time)
        self._last_tick_time = current_time
        
        with self._lock:
            self._frame_times.append(dt)
            self.frame_counter += 1
            avg_dt = sum(self._frame_times) / len(self._frame_times)
            self.fps = 1.0 / avg_dt if avg_dt > 0 else 0.0
        
        return dt

    def profile(self, section_name: str) -> ProfileContext:
        """Pythonic context manager for section timing: with monitor.profile('section'):"""
        return ProfileContext(self, section_name)

    def start_timer(self, name: str) -> None:
        """Starts a manual timer for a named section."""
        with self._lock:
            self._timers[name] = time.perf_counter()

    def stop_timer(self, name: str) -> float:
        """Stops a manual timer and records duration in milliseconds."""
        with self._lock:
            start_time = self._timers.pop(name, None)
        if start_time is None:
            return 0.0
        
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self.record_latency(name, duration_ms)
        return duration_ms

    def record_latency(self, name: str, duration_ms: float) -> None:
        """Thread-safely records a section latency duration in milliseconds."""
        with self._lock:
            if name not in self._section_latencies:
                self._section_latencies[name] = deque(maxlen=self.window_size)
            self._section_latencies[name].append(duration_ms)

    def get_average_latency(self, name: str) -> float:
        """Returns the rolling average latency of a section in milliseconds."""
        with self._lock:
            records = self._section_latencies.get(name)
            if not records:
                return 0.0
            return sum(records) / len(records)

    def get_snapshot(
        self,
        vision_stats: Optional[Any] = None,
        active_module_name: str = "none"
    ) -> ProfileSnapshot:
        """Generates an immutable ProfileSnapshot capturing current rolling performance metrics.

        Args:
            vision_stats: Optional VisionStats snapshot from VisionPipeline.
            active_module_name: Name of active hero module.

        Returns:
            ProfileSnapshot: Immutable data snapshot.
        """
        with self._lock:
            frame_id = self.frame_counter
            current_fps = self.fps
            avg_dt = (sum(self._frame_times) / len(self._frame_times)) * 1000.0 if self._frame_times else 0.0
            
            latencies_ms: Dict[str, float] = {}
            p95_latencies_ms: Dict[str, float] = {}
            
            for name, records in self._section_latencies.items():
                if records:
                    arr = np.array(records)
                    latencies_ms[name] = float(np.mean(arr))
                    p95_latencies_ms[name] = float(np.percentile(arr, 95))

        cpu_pct, mem_mb = self.system_provider.get_metrics()
        
        vision_fps = vision_stats.tracking_fps if vision_stats else None
        vision_lat = vision_stats.average_latency_ms if vision_stats else None

        return ProfileSnapshot(
            frame_id=frame_id,
            fps=current_fps,
            frame_time_ms=avg_dt,
            latencies_ms=latencies_ms,
            p95_latencies_ms=p95_latencies_ms,
            cpu_percent=cpu_pct,
            memory_mb=mem_mb,
            active_module_name=active_module_name,
            vision_fps=vision_fps,
            vision_latency_ms=vision_lat
        )

    def toggle_display(self) -> bool:
        """Toggles display/logging mode for the F3 hotkey without clearing metrics."""
        self.display_enabled = not self.display_enabled
        status = "ENABLED" if self.display_enabled else "DISABLED"
        logger.info(f"Performance Monitor HUD overlay output {status}.")
        return self.display_enabled

    def log_metrics(self, snapshot: Optional[ProfileSnapshot] = None) -> None:
        """Log performance snapshot metrics to standard output."""
        snap = snapshot or self.get_snapshot()
        lat_str = ", ".join(
            f"{k}: {v:.1f}ms (p95: {snap.p95_latencies_ms.get(k, 0.0):.1f}ms)"
            for k, v in snap.latencies_ms.items()
        )
        
        sys_str = ""
        if snap.cpu_percent is not None and snap.memory_mb is not None:
            sys_str = f" | CPU: {snap.cpu_percent:.1f}% | RAM: {snap.memory_mb:.1f}MB"
        elif snap.cpu_percent is None:
            sys_str = " | System Metrics: N/A"

        vis_str = ""
        if snap.vision_fps is not None:
            vis_str = f" | Vision FPS: {snap.vision_fps:.1f}"

        logger.info(
            f"[FPS: {snap.fps:.1f}{vis_str}{sys_str}] Module: '{snap.active_module_name}' | "
            f"FrameTime: {snap.frame_time_ms:.1f}ms | Latencies [{lat_str}]"
        )
