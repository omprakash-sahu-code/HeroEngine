import queue
import threading
import time
from typing import List, Dict, Any, Optional

from src.engine.network.models import TelemetryFrame
from src.engine.network.transport import Transport
from src.engine.network.bus import TelemetryBus
from src.engine.utils.logger import setup_logger

logger = setup_logger("NetworkDispatcher")

class NetworkDispatcher:
    """Orchestrates network transports via a Producer-Consumer thread and bounded latest-frame buffer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        
        # Bounded latest-frame buffer (maxsize=1 ensures ZERO queue stalls and drops stale frames instantly)
        self._queue: queue.Queue[TelemetryFrame] = queue.Queue(maxsize=1)
        self._transports: List[Transport] = []
        
        self._active = False
        self._worker_thread: Optional[threading.Thread] = None

        # Delta-tracking variables to eliminate frame spam
        self._last_module: Optional[str] = None
        self._last_gestures: Dict[str, str] = {}
        self._frame_counter = 0

    def add_transport(self, transport: Transport) -> None:
        """Register a network transport backend."""
        self._transports.append(transport)

    def attach_to_bus(self, bus: TelemetryBus) -> None:
        """Subscribe dispatcher to TelemetryBus topics."""
        bus.subscribe("frame", self._on_telemetry_frame)

    def _on_telemetry_frame(self, frame: TelemetryFrame) -> None:
        """Callback receiving TelemetryFrame instances from TelemetryBus."""
        self.push_frame(frame)

    def push_frame(self, frame: TelemetryFrame) -> None:
        """Push a telemetry frame to the bounded latest-frame queue without blocking."""
        if not self._enabled or not self._active:
            return

        # If queue is full, evict the stale frame immediately
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass

        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            pass

    def start(self) -> None:
        """Start all network transports and background dispatcher thread."""
        if not self._enabled:
            logger.info("NetworkDispatcher is disabled in configuration.")
            return

        for transport in self._transports:
            try:
                transport.start()
            except Exception as e:
                logger.error(f"Failed starting transport '{transport.name}': {e}")

        self._active = True
        self._worker_thread = threading.Thread(target=self._dispatcher_loop, daemon=True)
        self._worker_thread.start()
        logger.info("NetworkDispatcher background worker thread started.")

    def _dispatcher_loop(self) -> None:
        """Background loop popping frames from latest-frame buffer and dispatching to transports."""
        while self._active:
            try:
                frame = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            self._frame_counter += 1

            # Delta filtering: Only include module/gestures on change or periodic 60-frame heartbeat
            is_heartbeat = (self._frame_counter % 60 == 0)
            
            # Module delta check
            if not is_heartbeat and frame.module == self._last_module:
                filtered_module = None
            else:
                filtered_module = frame.module
                self._last_module = frame.module

            # Gesture delta check
            if not is_heartbeat and frame.gestures == self._last_gestures:
                filtered_gestures = {}
            else:
                filtered_gestures = dict(frame.gestures)
                self._last_gestures = dict(frame.gestures)

            # Create delta frame payload
            delta_frame = TelemetryFrame(
                timestamp=frame.timestamp,
                frame_number=frame.frame_number,
                hands=frame.hands,
                gestures=filtered_gestures,
                module=filtered_module,
                camera=frame.camera,
                effects=frame.effects,
                fps=frame.fps
            )

            # Dispatch to all active transports
            for transport in self._transports:
                if transport.is_active:
                    try:
                        transport.send(delta_frame)
                    except Exception as e:
                        logger.debug(f"Error sending frame via '{transport.name}': {e}")

    def stop(self) -> None:
        """Stop background worker thread and shut down all network transports."""
        self._active = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

        for transport in self._transports:
            try:
                transport.stop()
            except Exception as e:
                logger.error(f"Error stopping transport '{transport.name}': {e}")

        logger.info("NetworkDispatcher shut down cleanly.")
