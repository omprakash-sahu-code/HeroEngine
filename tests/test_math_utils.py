import unittest
import math
from unittest.mock import patch

from src.engine.utils.math import euclidean_distance_3d, calculate_angle_3d, lerp
from src.engine.utils.geometry import fit_circle_2d
from src.engine.utils.timers import DebounceTimer, CooldownTracker

class TestMathUtils(unittest.TestCase):
    """Unit tests for 3D vector math and interpolation utilities."""

    def test_euclidean_distance_3d_zero(self):
        p1 = (1.5, 2.5, -3.5)
        self.assertAlmostEqual(euclidean_distance_3d(p1, p1), 0.0)

    def test_euclidean_distance_3d_symmetry(self):
        p1 = (1.0, 2.0, 3.0)
        p2 = (-4.0, 5.0, -6.0)
        d1 = euclidean_distance_3d(p1, p2)
        d2 = euclidean_distance_3d(p2, p1)
        self.assertAlmostEqual(d1, d2)

    def test_euclidean_distance_3d_accuracy(self):
        # 3-4-5 triangle in 3D: (0,0,0) to (3,4,0) -> distance = 5
        d = euclidean_distance_3d((0.0, 0.0, 0.0), (3.0, 4.0, 0.0))
        self.assertAlmostEqual(d, 5.0)

    def test_euclidean_distance_3d_large_values(self):
        p1 = (1e6, 1e6, 1e6)
        p2 = (1e6 + 3.0, 1e6 + 4.0, 1e6)
        d = euclidean_distance_3d(p1, p2)
        self.assertAlmostEqual(d, 5.0)

    def test_calculate_angle_3d_right_angle(self):
        p1 = (1.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)
        p3 = (0.0, 1.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertAlmostEqual(angle, 90.0)

    def test_calculate_angle_3d_straight_line(self):
        p1 = (-1.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)
        p3 = (1.0, 0.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertAlmostEqual(angle, 180.0)

    def test_calculate_angle_3d_degenerate_vertex(self):
        # Zero length vector from vertex to p1
        p1 = (0.0, 0.0, 0.0)
        p2 = (0.0, 0.0, 0.0)
        p3 = (1.0, 0.0, 0.0)
        angle = calculate_angle_3d(p1, p2, p3)
        self.assertEqual(angle, 0.0)

    def test_lerp_invariants_and_clamping(self):
        a, b = 10.0, 20.0
        # Endpoint invariants
        self.assertAlmostEqual(lerp(a, b, 0.0), a)
        self.assertAlmostEqual(lerp(a, b, 1.0), b)
        self.assertAlmostEqual(lerp(a, b, 0.5), 15.0)
        # Clamping
        self.assertAlmostEqual(lerp(a, b, -0.5), a)
        self.assertAlmostEqual(lerp(a, b, 1.5), b)


class TestGeometryUtils(unittest.TestCase):
    """Unit tests for 2D algebraic circle fitting."""

    def test_fit_circle_ideal(self):
        # Generate 8 points on a circle centered at (2.0, 3.0) with radius 5.0
        angles = [i * (2 * math.pi / 8) for i in range(8)]
        points = [(2.0 + 5.0 * math.cos(a), 3.0 + 5.0 * math.sin(a)) for a in angles]

        res = fit_circle_2d(points)
        self.assertIsNotNone(res)
        xc, yc, r, variance = res
        self.assertAlmostEqual(xc, 2.0, places=4)
        self.assertAlmostEqual(yc, 3.0, places=4)
        self.assertAlmostEqual(r, 5.0, places=4)
        self.assertAlmostEqual(variance, 0.0, places=5)

    def test_fit_circle_insufficient_points(self):
        # Must return None if points < 5
        points = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (3.0, 1.0)]
        self.assertIsNone(fit_circle_2d(points))


class TestTimerUtils(unittest.TestCase):
    """Unit tests for DebounceTimer and CooldownTracker using mock time."""

    @patch("time.time")
    def test_debounce_timer(self, mock_time):
        mock_time.return_value = 100.0
        timer = DebounceTimer(required_duration=0.5)

        # Condition False -> Returns False
        self.assertFalse(timer.update(False))

        # Condition True -> First tick sets start_time = 100.0, elapsed = 0.0 < 0.5 -> False
        self.assertFalse(timer.update(True))

        # Advance time by 0.3s -> elapsed = 0.3 < 0.5 -> False
        mock_time.return_value = 100.3
        self.assertFalse(timer.update(True))

        # Advance time by 0.6s -> elapsed = 0.6 >= 0.5 -> True
        mock_time.return_value = 100.6
        self.assertTrue(timer.update(True))

        # Reset condition -> False and resets timer
        self.assertFalse(timer.update(False))
        self.assertIsNone(timer.start_time)

    @patch("time.time")
    def test_cooldown_tracker(self, mock_time):
        mock_time.return_value = 50.0
        tracker = CooldownTracker(cooldown_duration=1.0)

        # Initial state: not cooling down
        self.assertFalse(tracker.is_cooling_down())

        # First trigger succeeds
        self.assertTrue(tracker.trigger())
        self.assertTrue(tracker.is_cooling_down())

        # Immediate second trigger fails
        mock_time.return_value = 50.5
        self.assertFalse(tracker.trigger())

        # Advance time past 1.0s -> trigger succeeds
        mock_time.return_value = 51.1
        self.assertFalse(tracker.is_cooling_down())
        self.assertTrue(tracker.trigger())

if __name__ == "__main__":
    unittest.main()
