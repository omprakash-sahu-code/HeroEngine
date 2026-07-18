import unittest
import random
import numpy as np
from src.engine.gestures.recognizer import GestureRecognizer
from src.engine.core.input_manager import InputManager

class TestGestureRecognition(unittest.TestCase):
    """Tests heuristic geometric gesture classification algorithms."""

    def setUp(self):
        self.recognizer = GestureRecognizer()

def create_base_hand():
    """Creates flat baseline coordinates for a hand structure."""
    landmarks = [(0.0, 0.0, 0.0)] * 21
    landmarks[0] = (0.0, 0.0, 0.0)
    return landmarks

def create_open_palm_landmarks():
    landmarks = create_base_hand()
    # Wrist
    landmarks[0] = (0.0, 0.0, 0.0)
    landmarks[9] = (0.0, 0.2, 0.0) # Palm scale = 0.2
    
    # Thumb
    landmarks[1] = (0.1, 0.0, 0.0)
    landmarks[2] = (0.2, 0.0, 0.0)
    landmarks[3] = (0.3, 0.0, 0.0)
    landmarks[4] = (0.4, 0.0, 0.0)
    
    # Index
    landmarks[5] = (-0.05, 0.2, 0.0)
    landmarks[6] = (-0.05, 0.3, 0.0)
    landmarks[7] = (-0.05, 0.4, 0.0)
    landmarks[8] = (-0.05, 0.5, 0.0)

    # Middle
    landmarks[9] = (0.0, 0.2, 0.0)
    landmarks[10] = (0.0, 0.3, 0.0)
    landmarks[11] = (0.0, 0.4, 0.0)
    landmarks[12] = (0.0, 0.5, 0.0)

    # Ring
    landmarks[13] = (0.05, 0.2, 0.0)
    landmarks[14] = (0.05, 0.3, 0.0)
    landmarks[15] = (0.05, 0.4, 0.0)
    landmarks[16] = (0.05, 0.5, 0.0)

    # Pinky
    landmarks[17] = (0.1, 0.2, 0.0)
    landmarks[18] = (0.1, 0.3, 0.0)
    landmarks[19] = (0.1, 0.4, 0.0)
    landmarks[20] = (0.1, 0.5, 0.0)
    return landmarks

class TestGestureRecognition(unittest.TestCase):
    """Tests heuristic geometric gesture classification algorithms."""

    def setUp(self):
        self.recognizer = GestureRecognizer()

    def test_open_palm_detection(self):
        landmarks = create_open_palm_landmarks()
        gesture, conf = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "Open Palm")
        self.assertEqual(conf, 1.0)

    def test_closed_fist_detection(self):
        landmarks = create_base_hand()
        landmarks[0] = (0.0, 0.0, 0.0)
        landmarks[9] = (0.0, 0.2, 0.0)
        
        # Thumb curled
        landmarks[1] = (0.05, 0.0, 0.0)
        landmarks[2] = (0.08, 0.0, 0.0)
        landmarks[3] = (0.06, 0.0, 0.0)
        landmarks[4] = (0.04, 0.0, 0.0)

        # Index curled
        landmarks[5] = (-0.05, 0.2, 0.0)
        landmarks[6] = (-0.05, 0.15, 0.0)
        landmarks[7] = (-0.05, 0.1, 0.0)
        landmarks[8] = (-0.05, 0.05, 0.0)

        # Middle curled
        landmarks[9] = (0.0, 0.2, 0.0)
        landmarks[10] = (0.0, 0.15, 0.0)
        landmarks[11] = (0.0, 0.1, 0.0)
        landmarks[12] = (0.0, 0.05, 0.0)

        # Ring curled
        landmarks[13] = (0.05, 0.2, 0.0)
        landmarks[14] = (0.05, 0.15, 0.0)
        landmarks[15] = (0.05, 0.1, 0.0)
        landmarks[16] = (0.05, 0.05, 0.0)

        # Pinky curled
        landmarks[17] = (0.1, 0.2, 0.0)
        landmarks[18] = (0.1, 0.15, 0.0)
        landmarks[19] = (0.1, 0.1, 0.0)
        landmarks[20] = (0.1, 0.05, 0.0)

        gesture, conf = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "Closed Fist")

    def test_pinch_threshold_boundary(self):
        landmarks = create_base_hand()
        landmarks[0] = (0.0, 0.0, 0.0)
        landmarks[9] = (0.0, 0.2, 0.0) # palm scale = 0.2
        
        # Threshold ratio is 0.15 -> threshold dist = 0.15 * 0.2 = 0.03

        # Sub-threshold distance (0.025 / 0.2 = 0.125 < 0.15) -> Pinch
        landmarks[4] = (0.1, 0.1, 0.0)
        landmarks[8] = (0.125, 0.1, 0.0)
        gesture_sub, _ = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture_sub, "Pinch")

        # Above-threshold distance (0.04 / 0.2 = 0.20 > 0.15) -> Not Pinch
        landmarks[8] = (0.14, 0.1, 0.0)
        gesture_above, _ = self.recognizer.recognize(landmarks)
        self.assertNotEqual(gesture_above, "Pinch")

    def test_unknown_ambiguous_pose(self):
        # Pose with 2 fingers extended and 2 curled
        landmarks = create_base_hand()
        landmarks[0] = (0.0, 0.0, 0.0)
        landmarks[9] = (0.0, 0.2, 0.0)

        # Index and Middle extended
        landmarks[5] = (-0.05, 0.2, 0.0)
        landmarks[8] = (-0.05, 0.5, 0.0)
        landmarks[9] = (0.0, 0.2, 0.0)
        landmarks[12] = (0.0, 0.5, 0.0)

        # Ring and Pinky curled
        landmarks[13] = (0.05, 0.2, 0.0)
        landmarks[16] = (0.05, 0.05, 0.0)
        landmarks[17] = (0.1, 0.2, 0.0)
        landmarks[20] = (0.1, 0.05, 0.0)

        gesture, _ = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "None")

    def test_noise_jitter_tolerance(self):
        base_landmarks = create_open_palm_landmarks()

        # Add random noise (jitter) to all landmarks over 20 iterations
        random.seed(42)
        for _ in range(20):
            noisy_landmarks = [
                (x + random.uniform(-0.003, 0.003),
                 y + random.uniform(-0.003, 0.003),
                 z + random.uniform(-0.003, 0.003))
                for x, y, z in base_landmarks
            ]
            gesture, _ = self.recognizer.recognize(noisy_landmarks)
            self.assertEqual(gesture, "Open Palm")


class TestInputManager(unittest.TestCase):
    """Tests InputManager state updates, debouncing, 100-frame stability, and circular motion."""

    def test_debounce_logic(self):
        manager = InputManager({"debounce_frames": 3})
        
        raw_pinch = {
            "label": "Left",
            "score": 0.9,
            "landmarks": [(0.0, 0.0, 0.0)] * 21
        }
        raw_pinch["landmarks"][9] = (0.0, 0.2, 0.0)
        raw_pinch["landmarks"][4] = (0.1, 0.1, 0.0)
        raw_pinch["landmarks"][8] = (0.1, 0.1, 0.0)

        # Frame 1 & 2: Output stays None
        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "None")

        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "None")

        # Frame 3: Output changes to Pinch
        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "Pinch")

    def test_sequence_stability_100_frames(self):
        manager = InputManager({"debounce_frames": 3})
        
        open_landmarks = create_open_palm_landmarks()
        raw_palm = {
            "label": "Right",
            "score": 0.95,
            "landmarks": open_landmarks
        }

        # Update 100 consecutive frames
        for frame in range(100):
            manager.update([raw_palm])
            if frame >= 3:
                # Must maintain Open Palm continuously with zero flickering
                self.assertEqual(manager.get_hand("Right").gesture, "Open Palm")

    def test_circular_motion_detection(self):
        manager = InputManager()
        # Feed 15 frames of points along a circle of radius 0.2 centered at (0.5, 0.5)
        for i in range(15):
            angle = i * (2 * np.pi / 15)
            x = 0.5 + 0.2 * np.cos(angle)
            y = 0.5 + 0.2 * np.sin(angle)
            
            # Create a 21-point hand layout centered around (x, y)
            landmarks = [(x + j*0.001, y + j*0.001, 0.0) for j in range(21)]
            # Spread thumb [4] and index [8] so it doesn't trigger pinch
            landmarks[4] = (x + 0.1, y, 0.0)
            landmarks[8] = (x - 0.1, y, 0.0)
            landmarks[9] = (x, y, 0.0)
            
            raw_hand = {
                "label": "Left",
                "score": 0.9,
                "landmarks": landmarks
            }
            manager.update([raw_hand])

        is_circular, r, coverage = manager.check_circular_motion("Left")
        self.assertTrue(is_circular)
        self.assertAlmostEqual(r, 0.2, places=1)
        self.assertGreaterEqual(coverage, 1.5 * np.pi)

if __name__ == "__main__":
    unittest.main()
