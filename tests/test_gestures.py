import unittest
import numpy as np
from src.engine.gestures.recognizer import GestureRecognizer
from src.engine.core.input_manager import InputManager

class TestGestureRecognition(unittest.TestCase):
    """Tests the heuristic geometric gesture classification algorithms."""

    def setUp(self):
        self.recognizer = GestureRecognizer()

    def _create_base_hand(self):
        """Creates flat baseline coordinates for a hand structure."""
        # 21 points initialized to zero
        landmarks = [(0.0, 0.0, 0.0)] * 21
        # Wrist [0] at origin
        landmarks[0] = (0.0, 0.0, 0.0)
        return landmarks

    def test_open_palm_detection(self):
        """Open Palm: Fingertips are extended away from wrist further than knuckles."""
        landmarks = self._create_base_hand()
        # Wrist
        landmarks[0] = (0.0, 0.0, 0.0)
        
        # Thumb: MCP [2], IP [3], Tip [4] extended along positive X axis
        landmarks[1] = (0.1, 0.0, 0.0)
        landmarks[2] = (0.2, 0.0, 0.0)
        landmarks[3] = (0.3, 0.0, 0.0)
        landmarks[4] = (0.4, 0.0, 0.0)
        
        # Index: MCP [5], PIP [6], DIP [7], Tip [8] extended along Y axis
        landmarks[5] = (-0.05, 0.2, 0.0)
        landmarks[6] = (-0.05, 0.3, 0.0)
        landmarks[7] = (-0.05, 0.4, 0.0)
        landmarks[8] = (-0.05, 0.5, 0.0)

        # Middle: Knuckle [9] to Tip [12]
        landmarks[9] = (0.0, 0.2, 0.0)
        landmarks[10] = (0.0, 0.3, 0.0)
        landmarks[11] = (0.0, 0.4, 0.0)
        landmarks[12] = (0.0, 0.5, 0.0)

        # Ring: Knuckle [13] to Tip [16]
        landmarks[13] = (0.05, 0.2, 0.0)
        landmarks[14] = (0.05, 0.3, 0.0)
        landmarks[15] = (0.05, 0.4, 0.0)
        landmarks[16] = (0.05, 0.5, 0.0)

        # Pinky: Knuckle [17] to Tip [20]
        landmarks[17] = (0.1, 0.2, 0.0)
        landmarks[18] = (0.1, 0.3, 0.0)
        landmarks[19] = (0.1, 0.4, 0.0)
        landmarks[20] = (0.1, 0.5, 0.0)

        gesture, conf = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "Open Palm")
        self.assertEqual(conf, 1.0)

    def test_closed_fist_detection(self):
        """Closed Fist: fingertips folded back towards the wrist."""
        landmarks = self._create_base_hand()
        # Wrist at origin
        landmarks[0] = (0.0, 0.0, 0.0)
        
        # Thumb tip folded close to palm
        landmarks[1] = (0.05, 0.0, 0.0)
        landmarks[2] = (0.08, 0.0, 0.0)
        landmarks[3] = (0.06, 0.0, 0.0)
        landmarks[4] = (0.04, 0.0, 0.0)

        # Index knuckle [5] extended, tip [8] curled inside knuckle
        landmarks[5] = (-0.05, 0.2, 0.0)
        landmarks[6] = (-0.05, 0.15, 0.0)
        landmarks[7] = (-0.05, 0.1, 0.0)
        landmarks[8] = (-0.05, 0.05, 0.0)

        # Middle knuckle [9], tip [12] curled
        landmarks[9] = (0.0, 0.2, 0.0)
        landmarks[10] = (0.0, 0.15, 0.0)
        landmarks[11] = (0.0, 0.1, 0.0)
        landmarks[12] = (0.0, 0.05, 0.0)

        # Ring knuckle [13], tip [16] curled
        landmarks[13] = (0.05, 0.2, 0.0)
        landmarks[14] = (0.05, 0.15, 0.0)
        landmarks[15] = (0.05, 0.1, 0.0)
        landmarks[16] = (0.05, 0.05, 0.0)

        # Pinky knuckle [17], tip [20] curled
        landmarks[17] = (0.1, 0.2, 0.0)
        landmarks[18] = (0.1, 0.15, 0.0)
        landmarks[19] = (0.1, 0.1, 0.0)
        landmarks[20] = (0.1, 0.05, 0.0)

        gesture, conf = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "Closed Fist")

    def test_pinch_detection(self):
        """Pinch: Thumb tip [4] and Index tip [8] are very close."""
        landmarks = self._create_base_hand()
        # Wrist at origin, middle knuckle at (0, 0.2) -> scale factor
        landmarks[0] = (0.0, 0.0, 0.0)
        landmarks[9] = (0.0, 0.2, 0.0)
        
        # Place thumb tip [4] and index tip [8] at same location
        landmarks[4] = (0.1, 0.1, 0.0)
        landmarks[8] = (0.105, 0.1, 0.0) # distance = 0.005, ratio = 0.005/0.2 = 0.025 < 0.15

        gesture, conf = self.recognizer.recognize(landmarks)
        self.assertEqual(gesture, "Pinch")

class TestInputManager(unittest.TestCase):
    """Tests the InputManager state updates and debouncing."""

    def test_debounce_logic(self):
        manager = InputManager({"debounce_frames": 3})
        
        # Mocks a frame with index tip [8] and thumb tip [4] pinched
        raw_pinch = {
            "label": "Left",
            "score": 0.9,
            "landmarks": [(0.0, 0.0, 0.0)] * 21
        }
        # Set knuckle scale
        raw_pinch["landmarks"][9] = (0.0, 0.2, 0.0)
        raw_pinch["landmarks"][4] = (0.1, 0.1, 0.0)
        raw_pinch["landmarks"][8] = (0.1, 0.1, 0.0)

        # Frame 1: Candidate registers but output stays None (since debounce_frames=3)
        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "None")

        # Frame 2: Output stays None
        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "None")

        # Frame 3: Output changes to Pinch
        manager.update([raw_pinch])
        self.assertEqual(manager.get_hand("Left").gesture, "Pinch")

if __name__ == "__main__":
    unittest.main()
