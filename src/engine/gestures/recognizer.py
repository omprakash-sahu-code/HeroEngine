import math
from typing import List, Tuple, Dict, Any, Optional

class GestureRecognizer:
    """Evaluates geometric heuristics on hand landmarks to classify static gestures."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Sensitivity thresholds
        self.pinch_threshold = self.config.get("pinch_threshold", 0.15)
        self.palm_min_extension = self.config.get("palm_min_extension", 1.05)

    @staticmethod
    def _dist(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        """Calculate 3D Euclidean distance between two points."""
        return math.sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2 +
            (p1[2] - p2[2]) ** 2
        )

    def recognize(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[str, float]:
        """Classify gesture from list of 21 hand landmarks.

        Args:
            landmarks: List of (x, y, z) normalized coordinates.

        Returns:
            Tuple[str, float]: Detected gesture name ("Open Palm", "Closed Fist", "Pinch", or "None")
                               and the confidence score (always 1.0 for these heuristic checks).
        """
        if len(landmarks) < 21:
            return "None", 0.0

        # Calculate reference palm size scale (Wrist to Middle Knuckle/MCP)
        palm_scale = self._dist(landmarks[0], landmarks[9])
        if palm_scale < 1e-5:
            return "None", 0.0

        # 1. Check for Pinch (Distance between Thumb Tip [4] and Index Tip [8])
        pinch_dist = self._dist(landmarks[4], landmarks[8])
        is_pinch = (pinch_dist / palm_scale) < self.pinch_threshold

        if is_pinch:
            return "Pinch", 1.0

        # 2. Check for curled fingers to classify Fist vs Open Palm
        # Finger mappings: (tip, pip, mcp)
        fingers = [
            (8, 6, 5),   # Index
            (12, 10, 9), # Middle
            (16, 14, 13),# Ring
            (20, 18, 17) # Pinky
        ]

        curled_count = 0
        extended_count = 0

        for tip, pip, mcp in fingers:
            d_tip = self._dist(landmarks[0], landmarks[tip])
            d_pip = self._dist(landmarks[0], landmarks[pip])
            d_mcp = self._dist(landmarks[0], landmarks[mcp])

            # If tip is closer to wrist than PIP/MCP, it's curled
            if d_tip < d_pip or d_tip < d_mcp:
                curled_count += 1
            # If tip is significantly further from wrist than MCP, it's extended
            elif d_tip > d_mcp * self.palm_min_extension:
                extended_count += 1

        # Thumb check: Tip [4] to Pinky Knuckle [17] vs IP joint [3] to Pinky Knuckle [17]
        # Or simple distance from wrist
        d_thumb_tip = self._dist(landmarks[0], landmarks[4])
        d_thumb_mcp = self._dist(landmarks[0], landmarks[2])
        thumb_extended = d_thumb_tip > d_thumb_mcp * 1.1

        # Fist heuristic: All 4 main fingers curled
        if curled_count == 4:
            # Check if wrist (landmarks[0][1]) is raised overhead in top portion of frame (< 0.45)
            if landmarks[0][1] < 0.45:
                return "RAISED_CLOSED_FIST", 1.0
            return "Closed Fist", 1.0

        # INDEX_PINKY_EXTENDED heuristic: Index (8) & Pinky (20) extended, Middle (12) & Ring (16) curled
        d_index = self._dist(landmarks[0], landmarks[8])
        d_pinky = self._dist(landmarks[0], landmarks[20])
        d_middle = self._dist(landmarks[0], landmarks[12])
        d_ring = self._dist(landmarks[0], landmarks[16])
        
        index_ext = d_index > self._dist(landmarks[0], landmarks[5]) * self.palm_min_extension
        pinky_ext = d_pinky > self._dist(landmarks[0], landmarks[17]) * self.palm_min_extension
        middle_curled = d_middle < self._dist(landmarks[0], landmarks[10])
        ring_curled = d_ring < self._dist(landmarks[0], landmarks[14])

        if index_ext and pinky_ext and middle_curled and ring_curled:
            return "INDEX_PINKY_EXTENDED", 1.0

        # Open Palm heuristic: All 4 main fingers extended, and thumb extended
        if extended_count == 4 and thumb_extended:
            return "Open Palm", 1.0

        return "None", 0.0
