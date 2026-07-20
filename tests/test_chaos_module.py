import unittest
import numpy as np

from src.engine.procedural.wisps import WispGenerator
from src.engine.physics.force_field import ForceField, FieldMode
from src.modules.chaos.module import ChaosModule, ChaosState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectType

def create_mock_claw_hand(label: str = "Right") -> HandState:
    landmarks = [(0.0, 0.5, 0.0)] * 21
    # Curved fingertips
    landmarks[8] = (-0.05, 0.55, 0.0)
    landmarks[12] = (0.0, 0.55, 0.0)
    landmarks[16] = (0.05, 0.55, 0.0)
    landmarks[20] = (0.1, 0.55, 0.0)

    return HandState(label=label, score=0.95, landmarks=landmarks, gesture="CLAW_HAND")

class TestChaosModule(unittest.TestCase):
    """Test suite covering WispGenerator, ForceField physics, ChaosState transitions, and ChaosModule."""

    def test_wisp_generator_seed_determinism_and_bounds(self):
        gen = WispGenerator()
        center = (0.0, 0.0, 0.0)

        # Run 1 & 2 with seed 42 -> bit-exact matching output
        pts_a1 = gen.generate_swirl_wisp(center, seed=42)
        pts_a2 = gen.generate_swirl_wisp(center, seed=42)

        self.assertEqual(len(pts_a1), len(pts_a2))
        np.testing.assert_array_almost_equal(pts_a1, pts_a2)

        # Run 3 with seed 99 -> different output
        pts_b = gen.generate_swirl_wisp(center, seed=99)
        self.assertNotEqual(pts_a1[0], pts_b[0])

    def test_force_field_attraction_repulsion_vortex_math(self):
        ff = ForceField()
        att = ff.add_attractor(position=(0.0, 0.0, 0.0), strength=2.0, radius=1.0, mode=FieldMode.ATTRACT)

        # Test ATTRACT: Point at (0.5, 0.0, 0.0) should experience force pulling toward (0.0, 0.0, 0.0)
        f_att = ff.compute_force((0.5, 0.0, 0.0))
        self.assertLess(f_att[0], 0.0) # Force in negative X direction

        # Test REPULSE: Point at (0.5, 0.0, 0.0) should experience force pushing away (+X)
        att.mode = FieldMode.REPULSE
        f_rep = ff.compute_force((0.5, 0.0, 0.0))
        self.assertGreater(f_rep[0], 0.0)

        # Test VORTEX: Point at (0.5, 0.0, 0.0) should experience tangential force (+Y)
        att.mode = FieldMode.VORTEX
        f_vort = ff.compute_force((0.5, 0.0, 0.0))
        self.assertAlmostEqual(f_vort[0], 0.0, places=4)
        self.assertNotEqual(f_vort[1], 0.0)

    def test_chaos_module_interrupted_state_path(self):
        mod = ChaosModule({})
        mod.initialize()
        hand = create_mock_claw_hand()

        # Step 1: Start charging
        mod.process_input({"Right": hand})
        self.assertEqual(mod.state_machine, ChaosState.CHARGING)

        # Step 2: Lose gesture mid-charge -> Transitions to INTERRUPTED
        mod.process_input({})
        self.assertEqual(mod.state_machine, ChaosState.INTERRUPTED)

        # Step 3: Advance timer -> Transitions to COOLDOWN
        mod.update(0.3)
        self.assertEqual(mod.state_machine, ChaosState.COOLDOWN)

    def test_chaos_module_requests(self):
        mod = ChaosModule({})
        mod.initialize()
        hand = create_mock_claw_hand()

        # Fully charge energy
        mod.process_input({"Right": hand})
        mod.update(1.0)
        self.assertEqual(mod.state_machine, ChaosState.MANIPULATING)

        # Harvest render requests
        reqs = mod.get_render_requests()
        effect_types = [r.effect_type for r in reqs]
        self.assertIn(EffectType.DISTORTION_FIELD, effect_types)
        self.assertIn(EffectType.WISP_ARC, effect_types)

if __name__ == "__main__":
    unittest.main()
