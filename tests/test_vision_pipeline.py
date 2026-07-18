import unittest
import time
import numpy as np
from typing import Optional, List, Dict, Any

from src.engine.vision.types import (
    PipelineState,
    VisionResult,
    VisionStats,
    FrameSource,
    VisionProcessor
)
from src.engine.vision.pipeline import VisionPipeline

class MockFrameSource(FrameSource):
    """Mock FrameSource producing synthetic BGR numpy frames for testing."""
    def __init__(self, raise_error: bool = False, fail_reads: int = 0):
        self.raise_error = raise_error
        self.fail_reads = fail_reads
        self.started = False
        self.stopped = False

    def start(self) -> bool:
        self.started = True
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        if self.raise_error:
            raise RuntimeError("Mock camera error!")
        if self.fail_reads > 0:
            self.fail_reads -= 1
            return None
        # Return synthetic 100x100 BGR frame
        return np.zeros((100, 100, 3), dtype=np.uint8)

    def stop(self) -> None:
        self.stopped = True

class MockVisionProcessor(VisionProcessor):
    """Mock VisionProcessor returning dummy landmark data for testing."""
    def __init__(self, raise_error: bool = False):
        self.raise_error = raise_error
        self.initialized = False
        self.released = False

    def initialize(self) -> None:
        self.initialized = True

    def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        if self.raise_error:
            raise ValueError("Mock detector error!")
        return [{"label": "Right", "score": 0.99, "landmarks": [(0.5, 0.5, 0.0)]}]

    def release(self) -> None:
        self.released = True

class TestVisionPipeline(unittest.TestCase):
    """Test suite covering VisionPipeline multithreading, immutability, stats, and error recovery."""

    def test_pipeline_lifecycle_and_idempotency(self):
        source = MockFrameSource()
        processor = MockVisionProcessor()
        pipeline = VisionPipeline(source, processor)

        # Before start
        self.assertEqual(pipeline.state, PipelineState.STOPPED)
        self.assertIsNone(pipeline.get_latest_result())

        # Start pipeline
        self.assertTrue(pipeline.start())
        self.assertTrue(pipeline.start()) # Double start safety check

        # Wait for frame processing
        time.sleep(0.15)
        self.assertEqual(pipeline.state, PipelineState.RUNNING)

        # Fetch latest result
        result = pipeline.get_latest_result()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, VisionResult)
        self.assertFalse(result.frame.flags.writeable) # Immutability check
        self.assertGreater(result.frame_id, 0)
        self.assertEqual(len(result.hands_data), 1)

        # Verify stats
        stats = pipeline.get_stats()
        self.assertIsInstance(stats, VisionStats)
        self.assertGreater(stats.total_overwrites, 0)

        # Stop pipeline
        pipeline.stop()
        pipeline.stop() # Double stop safety check
        self.assertEqual(pipeline.state, PipelineState.STOPPED)
        self.assertTrue(source.stopped)
        self.assertTrue(processor.released)

    def test_camera_disconnect_and_dropped_frames_recovery(self):
        # FrameSource fails initial 3 reads (simulating camera disconnect) then succeeds
        source = MockFrameSource(fail_reads=3)
        processor = MockVisionProcessor()
        pipeline = VisionPipeline(source, processor)

        pipeline.start()
        time.sleep(0.3)

        # Pipeline should remain running and accumulate dropped_frames count without crashing!
        stats = pipeline.get_stats()
        self.assertGreaterEqual(stats.dropped_frames, 3)
        self.assertIsNotNone(pipeline.get_latest_result())

        pipeline.stop()

    def test_processor_exception_safety(self):
        # Processor raises exceptions on every frame
        source = MockFrameSource()
        processor = MockVisionProcessor(raise_error=True)
        pipeline = VisionPipeline(source, processor)

        pipeline.start()
        time.sleep(0.15)

        # Worker thread must NOT crash even when processor raises exceptions
        self.assertEqual(pipeline.state, PipelineState.RUNNING)

        pipeline.stop()
        self.assertEqual(pipeline.state, PipelineState.STOPPED)

if __name__ == "__main__":
    unittest.main()
