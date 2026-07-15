import time
from typing import Dict, List
from src.engine.utils.logger import setup_logger

logger = setup_logger("Monitor")

class PerformanceMonitor:
    """Measures and logs system framerates (FPS) and component execution latencies."""

    def __init__(self, avg_window: int = 30):
        """Args:

            avg_window: Number of frames over which to average metrics.
        """
        self.avg_window = avg_window
        self.frame_times: List[float] = []
        self.last_frame_time = time.time()
        
        self.timers: Dict[str, float] = {}
        self.latencies: Dict[str, List[float]] = {}
        
        self.fps = 0.0

    def tick(self) -> float:
        """Call at the start of each frame loop to update FPS metrics.

        Returns:
            float: Elapsed time since last tick in seconds (dt).
        """
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        self.frame_times.append(dt)
        if len(self.frame_times) > self.avg_window:
            self.frame_times.pop(0)
            
        avg_dt = sum(self.frame_times) / len(self.frame_times)
        self.fps = 1.0 / avg_dt if avg_dt > 0 else 0.0
        
        return dt

    def start_timer(self, name: str) -> None:
        """Start a stopwatch for a specific component.

        Args:
            name: Label identifier (e.g. 'vision', 'render').
        """
        self.timers[name] = time.perf_counter()

    def stop_timer(self, name: str) -> float:
        """Stop the stopwatch and record latency in milliseconds.

        Args:
            name: Label identifier.

        Returns:
            float: Duration in milliseconds.
        """
        if name not in self.timers:
            return 0.0
            
        start_time = self.timers.pop(name)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        if name not in self.latencies:
            self.latencies[name] = []
            
        self.latencies[name].append(duration_ms)
        if len(self.latencies[name]) > self.avg_window:
            self.latencies[name].pop(0)
            
        return duration_ms

    def get_average_latency(self, name: str) -> float:
        """Returns the rolling average latency of a component.

        Args:
            name: Label identifier.

        Returns:
            float: Average duration in milliseconds, or 0.0 if not recorded.
        """
        records = self.latencies.get(name)
        if not records:
            return 0.0
        return sum(records) / len(records)

    def log_metrics(self) -> None:
        """Log average performance numbers to standard output."""
        latencies_str = ", ".join(
            f"{name}: {self.get_average_latency(name):.1f}ms"
            for name in self.latencies
        )
        logger.info(f"Performance - FPS: {self.fps:.1f} | Latencies [{latencies_str}]")
