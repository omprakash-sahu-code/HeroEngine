from typing import Dict, Any, List
from src.engine.utils.logger import setup_logger

logger = setup_logger("SegmentationDetector")

class SegmentationDetector:
    """Wrapper class around MediaPipe Selfie Segmentation solution."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.segmentation_instance = None

    def initialize(self) -> None:
        logger.info("Initializing MediaPipe Selfie Segmentation model...")

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        return []

    def release(self) -> None:
        if self.segmentation_instance:
            self.segmentation_instance.close()
