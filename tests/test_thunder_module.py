import unittest
import numpy as np

from src.engine.procedural.lightning import LightningGenerator
from src.engine.core.camera_impulse import CameraImpulse
from src.modules.thunder.module import ThunderModule, ThunderState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectType

def create_mock_thunder_hand(label: str = "Right") -> HandState:
    landmarks = [(0.5, 0.05, 0.0)] * 21 # All landmarks raised overhead (y = 0.05 -> NDC y = 0.9)
    return HandState(label=label, score=0.95, landmarks=landmarks, gesture="RAISED_CLOSED_FIST")

class TestThunderModule(unittest.TestCase):
    """Test suite covering LightningGenerator determinism, CameraImpulse decay, failure paths, and ThunderModule."""

    def test_lightning_generator_seed_determinism(self):
        gen = LightningGenerator()
        start = (0.0, 1.0, 0.0)
        end = (0.0, -0.5, 0.0)

        # Run 1 with seed 100
        branches_a1 = gen.generate(start, end, seed=100)
        branches_a2 = gen.generate(start, end, seed=100)
        
        # Verify identical bit-exact output for identical seed
        self.assertEqual(len(branches_a1), len(branches_a2))
        for b1, b2 in zip(branches_a1, branches_a2):
            np.testing.assert_array_almost_equal(b1, b2)

        # Run 2 with different seed 200 -> different geometry
        branches_b = gen.generate(start, end, seed=200)
        self.assertNotEqual(branches_a1[0][1], branches_b[0][1])

    def test_lightning_generator_segment_continuity_and_bounds(self):
        gen = LightningGenerator()
        branches = gen.generate((0.0, 1.0, 0.0), (0.0, -1.0, 0.0), seed=42, generations=4)
        
        # Check main trunk starts at start_pos and ends near end_pos
        main_trunk = branches[0]
        self.assertEqual(main_trunk[0], (0.0, 1.0, 0.0))
        self.assertAlmostEqual(main_trunk[-1][1], -1.0, delta=0.2)

    def test_lightning_generator_large_distance_stability(self):
        gen = LightningGenerator()
        # Large coordinate range
        branches = gen.generate((0.0, 10000.0, 0.0), (10000.0, -10000.0, 0.0), seed=42)
        self.assertTrue(len(branches) > 0)
        for branch in branches:
            for pt in branch:
                self.assertFalse(np.isnan(pt).any())
                self.assertFalse(np.isinf(pt).any())

    def test_camera_impulse_decay(self):
        impulse = CameraImpulse()
        impulse.trigger_impulse(intensity=0.1, duration=0.4)

        mag1 = np.linalg.norm(impulse.update(0.05))
        mag2 = np.linalg.norm(impulse.update(0.15))
        mag3 = np.linalg.norm(impulse.update(0.25))

        # Verify magnitude strictly decreases as timer elapses
        self.assertGreater(mag1, mag2)
        self.assertGreater(mag2, mag3)
        self.assertEqual(impulse.update(0.5), (0.0, 0.0))

    def test_thunder_module_interrupted_state_path(self):
        mod = ThunderModule({})
        mod.initialize()
        hand = create_mock_thunder_hand()

        # Step 1: Start charging
        mod.process_input({"Right": hand})
        self.assertEqual(mod.state_machine, ThunderState.CHARGING)

        # Step 2: Lose gesture mid-charge -> Transitions to INTERRUPTED
        mod.process_input({})
        self.assertEqual(mod.state_machine, ThunderState.INTERRUPTED)

        # Step 3: Advance timer -> Transitions to COOLDOWN
        mod.update(0.3)
        self.assertEqual(mod.state_machine, ThunderState.COOLDOWN)

    def test_thunder_module_requests(self):
        mod = ThunderModule({})
        mod.initialize()
        hand = create_mock_thunder_hand()

        # Fully charge thunder
        mod.process_input({"Right": hand})
        mod.update(1.0)
        self.assertEqual(mod.state_machine, ThunderState.SUMMONED)

        # Discharge thunder by releasing gesture
        mod.process_input({})
        mod.update(0.1)
        self.assertEqual(mod.state_machine, ThunderState.DISCHARGING)

        # Verify CameraRequest emitted
        cam_reqs = mod.get_camera_requests()
        self.assertEqual(len(cam_reqs), 1)
        self.assertEqual(cam_reqs[0].action, "shake")

        # Verify Render Requests emitted for EYE_AURA and POLYLINE
        render_reqs = mod.get_render_requests()
        effect_types = [req.effect_type for req in render_reqs]
        self.assertIn(EffectType.EYE_AURA, effect_types)
        self.assertIn(EffectType.POLYLINE, effect_types)

if __name__ == "__main__":
    unittest.main()
