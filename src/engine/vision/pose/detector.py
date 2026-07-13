from typing import Dict, Any, List
from src.engine.utils.logger import setup_logger

logger = setup_logger("PoseDetector")

class PoseDetector:
    """Wrapper class around MediaPipe Pose solution."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pose_instance = None

    def initialize(self) -> None:
        logger.info("Initializing MediaPipe Pose model...")

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        return []

    def release(self) -> None:
        if self.pose_instance:
            self.pose_instance.close()
