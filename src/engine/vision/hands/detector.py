import cv2
import mediapipe as mp
from typing import Dict, Any, List, Optional
from src.engine.utils.logger import setup_logger
from src.engine.vision.types import VisionProcessor

logger = setup_logger("HandDetector")

class HandDetector(VisionProcessor):
    """Wrapper class around MediaPipe Hands solution."""

    def __init__(self, config: Dict[str, Any]):
        """Args:

            config: Dynamic configurations for hand detector.
        """
        self.config = config
        self.max_num_hands = config.get("max_num_hands", 2)
        self.min_detection_confidence = config.get("min_detection_confidence", 0.7)
        self.min_tracking_confidence = config.get("min_tracking_confidence", 0.7)
        
        self.mp_hands = None
        self.hands_instance = None

    def initialize(self) -> None:
        """Initialize the MediaPipe Hand tracking resources."""
        logger.info("Initializing MediaPipe Hand tracking model...")
        try:
            self.mp_hands = mp.solutions.hands
            self.hands_instance = self.mp_hands.Hands(
                max_num_hands=self.max_num_hands,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            logger.info("MediaPipe Hand tracking initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to initialize MediaPipe Hand tracking: {e}")
            raise e

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        """Processes an image frame and returns detected hand landmarks.

        Args:
            frame: OpenCV image frame (BGR format).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing hand type
                                  (Left/Right), score, and 21 normalized landmarks.
        """
        if not self.hands_instance or frame is None:
            return []

        # MediaPipe requires RGB images
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands_instance.process(rgb_frame)
        
        hands_data = []
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Format landmarks list
                landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                
                # Get hand label (MediaPipe flipped handedness: Left/Right label refers to video perspective)
                label = handedness.classification[0].label
                score = handedness.classification[0].score
                
                hands_data.append({
                    "label": label,
                    "score": score,
                    "landmarks": landmarks
                })
                
        return hands_data

    def release(self) -> None:
        """Releases the underlying MediaPipe models."""
        if self.hands_instance:
            self.hands_instance.close()
            self.hands_instance = None
            logger.info("MediaPipe Hand tracking closed.")

