from typing import Dict, Any, List
from src.engine.utils.logger import setup_logger

logger = setup_logger("FaceDetector")

class FaceDetector:
    """Wrapper class around MediaPipe Face Mesh solution."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.face_mesh_instance = None

    def initialize(self) -> None:
        logger.info("Initializing MediaPipe Face Mesh model...")

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        return []

    def release(self) -> None:
        if self.face_mesh_instance:
            self.face_mesh_instance.close()
