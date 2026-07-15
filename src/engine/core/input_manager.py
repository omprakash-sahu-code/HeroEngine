import time
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from src.engine.gestures.recognizer import GestureRecognizer
from src.engine.utils.logger import setup_logger

logger = setup_logger("InputManager")

class HandState:
    """Represents the processed state of a tracked hand in HeroEngine."""

    def __init__(self, label: str, score: float, landmarks: List[Tuple[float, float, float]], gesture: str):
        self.label = label  # "Left" or "Right"
        self.score = score  # Tracking confidence score (0.0 to 1.0)
        self.landmarks = landmarks  # List of 21 raw normalized landmarks
        self.gesture = gesture  # Debounced gesture name
        
        # Calculate raw centroid (average of all landmarks)
        pts = np.array(landmarks)
        self.centroid = tuple(np.mean(pts, axis=0).tolist())  # (x, y, z)
        
        # Calculate pinch distance (normalized thumb to index tip distance)
        palm_scale = math_dist(landmarks[0], landmarks[9])
        self.pinch_distance = math_dist(landmarks[4], landmarks[8]) / max(palm_scale, 1e-5)
        
        # Velocity computed by InputManager (defaults to zero)
        self.velocity = (0.0, 0.0, 0.0)

    def get_landmark_ndc(self, idx: int) -> Tuple[float, float, float]:
        """Convert a landmark's coordinates from MediaPipe normalized space to OpenGL NDC."""
        if idx < 0 or idx >= len(self.landmarks):
            return (0.0, 0.0, 0.0)
        x, y, z = self.landmarks[idx]
        # X: [0..1] -> [-1..1]
        x_ndc = (x * 2.0) - 1.0
        # Y: [0..1] -> [1..-1] (flip Y axis)
        y_ndc = 1.0 - (y * 2.0)
        # Z: Keep scaled
        z_ndc = z
        return (x_ndc, y_ndc, z_ndc)

    def get_centroid_ndc(self) -> Tuple[float, float, float]:
        """Convert hand's centroid from MediaPipe space to OpenGL NDC."""
        x, y, z = self.centroid
        return ((x * 2.0) - 1.0, 1.0 - (y * 2.0), z)


def math_dist(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return np.linalg.norm(np.array(p1) - np.array(p2))


class InputManager:
    """Tracks raw inputs from HandDetector, manages temporal history buffers,

    applies gesture debouncing, and computes dynamic features (velocity, circle fits).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        gesture_config = self.config.get("gestures", {})
        self.recognizer = GestureRecognizer(gesture_config)
        
        # Configuration settings
        self.history_size = self.config.get("history_size", 30)  # 30 frames
        self.debounce_frames = self.config.get("debounce_frames", 3)  # Consecutive frames to register gesture
        
        # Running state history per hand: label -> list of raw frame data
        # raw frame data dictionary: {"landmarks": ..., "timestamp": ..., "raw_gesture": ...}
        self.history: Dict[str, List[Dict[str, Any]]] = {
            "Left": [],
            "Right": []
        }
        
        # Debounce states: label -> {"current": gesture, "candidate": gesture, "counter": int}
        self.debounce_states: Dict[str, Dict[str, Any]] = {
            "Left": {"current": "None", "candidate": "None", "counter": 0},
            "Right": {"current": "None", "candidate": "None", "counter": 0}
        }
        
        # Final processed states for the current frame
        self.active_hands: Dict[str, HandState] = {}

    def update(self, raw_hands_data: List[Dict[str, Any]]) -> None:
        """Process a new frame's raw hand detections, updating buffers and states.

        Args:
            raw_hands_data: Output list from HandDetector.process_frame.
        """
        current_time = time.perf_counter()
        
        # Keep track of which hands were detected in this frame
        detected_labels = []
        
        for raw_hand in raw_hands_data:
            label = raw_hand["label"]  # "Left" or "Right"
            landmarks = raw_hand["landmarks"]
            score = raw_hand["score"]
            detected_labels.append(label)
            
            # Evaluate static gesture heuristic
            raw_gesture, _ = self.recognizer.recognize(landmarks)
            
            # Append to history buffer
            hist_item = {
                "landmarks": landmarks,
                "timestamp": current_time,
                "raw_gesture": raw_gesture,
                "centroid": np.mean(np.array(landmarks), axis=0).tolist()
            }
            self.history[label].append(hist_item)
            if len(self.history[label]) > self.history_size:
                self.history[label].pop(0)
                
            # Resolve gesture debouncing
            deb = self.debounce_states[label]
            if raw_gesture == deb["candidate"]:
                deb["counter"] += 1
            else:
                deb["candidate"] = raw_gesture
                deb["counter"] = 1
                
            if deb["counter"] >= self.debounce_frames:
                deb["current"] = raw_gesture
                
            # Create finalized HandState
            hand_state = HandState(label, score, landmarks, deb["current"])
            
            # Compute velocity using history buffer (look back 5 frames or maximum available)
            hist = self.history[label]
            if len(hist) > 1:
                lookback = min(5, len(hist) - 1)
                prev_item = hist[-1 - lookback]
                dt = current_time - prev_item["timestamp"]
                if dt > 1e-5:
                    dp = np.array(hist_item["centroid"]) - np.array(prev_item["centroid"])
                    hand_state.velocity = tuple((dp / dt).tolist())
                    
            self.active_hands[label] = hand_state

        # Clear state/history for hands that have disappeared
        for label in ["Left", "Right"]:
            if label not in detected_labels:
                self.history[label].clear()
                self.debounce_states[label] = {"current": "None", "candidate": "None", "counter": 0}
                if label in self.active_hands:
                    del self.active_hands[label]

    def get_hand(self, label: str) -> Optional[HandState]:
        """Get the processed HandState of a specific hand, if active."""
        return self.active_hands.get(label)

    def get_hands(self) -> Dict[str, HandState]:
        """Get all currently active HandStates."""
        return self.active_hands

    def check_circular_motion(self, label: str, min_points: int = 15) -> Tuple[bool, float, float]:
        """Perform circle fitting on the hand's centroid history to detect circular motion (Portals).

        Args:
            label: "Left" or "Right"
            min_points: Minimum number of historical frames required to evaluate.

        Returns:
            Tuple[bool, float, float]: (is_circular, radius, angular_coverage)
        """
        hist = self.history[label]
        if len(hist) < min_points:
            return False, 0.0, 0.0
            
        # Extract 2D coordinates (X, Y)
        points = np.array([item["centroid"][:2] for item in hist])
        
        # Calculate centroid of points
        center = np.mean(points, axis=0)
        
        # Calculate average radius
        radii = np.linalg.norm(points - center, axis=1)
        avg_radius = np.mean(radii)
        if avg_radius < 1e-4:
            return False, 0.0, 0.0
            
        # Calculate radial variance
        variance = np.mean((radii - avg_radius) ** 2)
        relative_variance = variance / (avg_radius ** 2)
        
        # Threshold: circle variance must be small
        if relative_variance > 0.05:  # Maximum 5% deviation from true circle
            return False, avg_radius, 0.0
            
        # Calculate angular coverage around center to ensure a complete circular arc
        angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
        # Unwrap angles to handle boundary crossings
        angles = np.unwrap(angles)
        angular_coverage = abs(np.max(angles) - np.min(angles))
        
        # Circular check: must span at least 1.5 * pi radians (270 degrees) to be considered circular path
        is_circular = angular_coverage > 1.5 * np.pi
        
        return is_circular, avg_radius, angular_coverage
