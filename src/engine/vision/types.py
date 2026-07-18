from abc import ABC, abstractmethod
from enum import IntEnum
from dataclasses import dataclass
from typing import Tuple, Dict, Any, List, Optional
import numpy as np

class PipelineState(IntEnum):
    """Lifecycle states for asynchronous VisionPipeline worker."""
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    STOPPING = 3

@dataclass(frozen=True)
class VisionResult:
    """Immutable data container for vision frame and tracking results."""
    frame: np.ndarray
    hands_data: Tuple[Dict[str, Any], ...]
    frame_id: int
    capture_timestamp: float
    processing_start: float
    processing_end: float

    @property
    def tracking_latency_ms(self) -> float:
        """Time spent executing vision detector inference in milliseconds."""
        return max(0.0, (self.processing_end - self.processing_start) * 1000.0)

    @property
    def total_pipeline_latency_ms(self) -> float:
        """Total time elapsed from frame capture to result completion in milliseconds."""
        return max(0.0, (self.processing_end - self.capture_timestamp) * 1000.0)

@dataclass
class VisionStats:
    """Live performance metrics for VisionPipeline."""
    capture_fps: float = 0.0
    tracking_fps: float = 0.0
    average_latency_ms: float = 0.0
    dropped_frames: int = 0
    total_overwrites: int = 0

class FrameSource(ABC):
    """Abstract interface for video frame ingestion sources (camera, video file, mock)."""

    @abstractmethod
    def start(self) -> bool:
        """Starts frame ingestion."""
        pass

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """Reads the latest frame (BGR numpy array)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops frame ingestion and cleans up resources."""
        pass

class VisionProcessor(ABC):
    """Abstract interface for vision tracking processors (MediaPipe hands, pose, face)."""

    @abstractmethod
    def initialize(self) -> None:
        """Initializes underlying vision models."""
        pass

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Processes a frame and returns structured tracking landmark data."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases underlying vision model resources."""
        pass
