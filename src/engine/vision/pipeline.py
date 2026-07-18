import threading
import time
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

from src.engine.utils.logger import setup_logger
from src.engine.vision.types import (
    PipelineState,
    VisionResult,
    VisionStats,
    FrameSource,
    VisionProcessor
)

logger = setup_logger("VisionPipeline")

class VisionPipeline:
    """Asynchronous vision processing pipeline orchestrating frame ingestion and model inference

    on a dedicated background worker thread with atomic latest-result semantics.
    """

    def __init__(self, source: FrameSource, processor: VisionProcessor):
        """Args:

            source: Concrete implementation of FrameSource (webcam, video file, mock).
            processor: Concrete implementation of VisionProcessor (MediaPipe hands, pose, face).
        """
        self.source = source
        self.processor = processor
        self.state = PipelineState.STOPPED
        
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self._latest_result: Optional[VisionResult] = None
        self._stats = VisionStats()
        self._frame_id_counter = 0

    def start(self) -> bool:
        """Starts the background worker thread idempotently.

        Returns:
            bool: True if pipeline is running or started successfully.
        """
        with self._lock:
            if self.state in (PipelineState.STARTING, PipelineState.RUNNING):
                logger.warning("VisionPipeline is already running or starting.")
                return True
            self.state = PipelineState.STARTING

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="VisionPipelineWorker")
        self._thread.start()

        with self._lock:
            self.state = PipelineState.RUNNING
        logger.info("VisionPipeline background worker started successfully.")
        return True

    def _worker_loop(self) -> None:
        """Background worker thread executing frame capture and inference loop asynchronously."""
        logger.info("VisionPipeline worker thread initializing components...")
        
        try:
            self.source.start()
        except Exception as e:
            logger.error(f"Error starting FrameSource: {e}")

        try:
            self.processor.initialize()
        except Exception as e:
            logger.error(f"Error initializing VisionProcessor: {e}")

        last_fps_calc_time = time.perf_counter()
        frames_this_second = 0
        latency_samples: List[float] = []

        while not self._stop_event.is_set():
            loop_start = time.perf_counter()

            # 1. Ingest frame from source
            try:
                frame = self.source.read_frame()
            except Exception as read_err:
                logger.warning(f"Error reading frame from source: {read_err}")
                frame = None

            if frame is None:
                with self._lock:
                    self._stats.dropped_frames += 1
                # Camera disconnected or empty frame read - wait before retrying (auto-reconnect recovery)
                time.sleep(0.05)
                continue

            capture_timestamp = loop_start
            processing_start = time.perf_counter()

            # 2. Run vision inference asynchronously
            hands_data: List[Dict[str, Any]] = []
            try:
                hands_data = self.processor.process_frame(frame)
            except Exception as proc_err:
                logger.error(f"Error inside VisionProcessor.process_frame: {proc_err}", exc_info=True)

            processing_end = time.perf_counter()

            # 3. Create immutable read-only frame copy
            frame_copy = frame.copy()
            frame_copy.flags.writeable = False

            # 4. Construct immutable VisionResult
            self._frame_id_counter += 1
            result = VisionResult(
                frame=frame_copy,
                hands_data=tuple(hands_data),
                frame_id=self._frame_id_counter,
                capture_timestamp=capture_timestamp,
                processing_start=processing_start,
                processing_end=processing_end
            )

            # 5. Atomic write to latest_result
            with self._lock:
                self._latest_result = result
                self._stats.total_overwrites += 1

            # 6. Calculate performance metrics
            latency_ms = result.tracking_latency_ms
            latency_samples.append(latency_ms)
            if len(latency_samples) > 30:
                latency_samples.pop(0)

            frames_this_second += 1
            now = time.perf_counter()
            if now - last_fps_calc_time >= 1.0:
                calc_duration = now - last_fps_calc_time
                fps = frames_this_second / calc_duration
                avg_lat = sum(latency_samples) / len(latency_samples) if latency_samples else 0.0
                
                with self._lock:
                    self._stats.tracking_fps = fps
                    self._stats.capture_fps = fps
                    self._stats.average_latency_ms = avg_lat

                frames_this_second = 0
                last_fps_calc_time = now

            # Yield CPU briefly to prevent thread starvation
            time.sleep(0.001)

        # Worker shutdown cleanup
        logger.info("VisionPipeline worker shutting down...")
        try:
            self.processor.release()
        except Exception as e:
            logger.error(f"Error releasing VisionProcessor: {e}")

        try:
            self.source.stop()
        except Exception as e:
            logger.error(f"Error stopping FrameSource: {e}")

        with self._lock:
            self.state = PipelineState.STOPPED
        logger.info("VisionPipeline background worker stopped cleanly.")

    def get_latest_result(self) -> Optional[VisionResult]:
        """Atomically retrieves the latest processed VisionResult without blocking.

        Returns:
            Optional[VisionResult]: Latest result or None if no frame has been processed yet.
        """
        with self._lock:
            return self._latest_result

    def get_stats(self) -> VisionStats:
        """Returns a snapshot of current live pipeline statistics."""
        with self._lock:
            return VisionStats(
                capture_fps=self._stats.capture_fps,
                tracking_fps=self._stats.tracking_fps,
                average_latency_ms=self._stats.average_latency_ms,
                dropped_frames=self._stats.dropped_frames,
                total_overwrites=self._stats.total_overwrites
            )

    def stop(self) -> None:
        """Safely stops the worker thread idempotently."""
        with self._lock:
            if self.state in (PipelineState.STOPPED, PipelineState.STOPPING):
                return
            self.state = PipelineState.STOPPING

        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        with self._lock:
            self.state = PipelineState.STOPPED
        logger.info("VisionPipeline stopped.")
