import unittest
import numpy as np

from src.engine.physics.constraints import PointMass, DistanceConstraint, VerletRope
from src.engine.core.attachment import AttachmentTarget
from src.modules.spider.web_controller import WebController, WebLineState
from src.modules.spider.module import SpiderModule
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectType

def create_mock_spider_hand(label: str = "Right") -> HandState:
    landmarks = [(0.5, 0.5, 0.0)] * 21
    landmarks[0] = (0.5, 0.8, 0.0)
    landmarks[8] = (0.5, 0.2, 0.0)  # Index extended
    landmarks[20] = (0.5, 0.2, 0.0) # Pinky extended
    landmarks[12] = (0.5, 0.7, 0.0) # Middle curled
    landmarks[16] = (0.5, 0.7, 0.0) # Ring curled

    return HandState(label=label, score=0.95, landmarks=landmarks, gesture="INDEX_PINKY_EXTENDED")

class TestSpiderModule(unittest.TestCase):
    """Test suite covering Verlet physics, WebController state machine, failure paths, and SpiderModule."""

    def test_verlet_rope_constraint_preservation(self):
        start = (0.0, 1.0, 0.0)
        end = (0.0, 0.0, 0.0)
        rope = VerletRope(start, end, segment_count=10, stiffness=1.0)
        
        # Step physics 10 frames
        for _ in range(10):
            rope.step(0.016)

        # Verify distance constraints preserved
        for c in rope.constraints:
            dist = np.linalg.norm(c.p2.position - c.p1.position)
            self.assertAlmostEqual(dist, c.rest_length, delta=0.01)

    def test_verlet_rope_1000_frame_stability(self):
        rope = VerletRope((0.0, 1.0, 0.0), (1.0, 1.0, 0.0), segment_count=15)
        
        for _ in range(1000):
            rope.step(0.016)

        positions = rope.get_point_positions()
        for pos in positions:
            self.assertFalse(np.isnan(pos).any(), "NaN found in rope simulation!")
            self.assertFalse(np.isinf(pos).any(), "Inf found in rope simulation!")

    def test_web_controller_shooting_and_attachment(self):
        ctrl = WebController()
        target = AttachmentTarget(position=(0.0, 1.0, 0.0), confidence=0.9)

        # Trigger shoot
        ctrl.shoot((0.0, 0.0, 0.0), target)
        self.assertEqual(ctrl.state, WebLineState.SHOOTING)

        # Step projectile travel to target
        while ctrl.state == WebLineState.SHOOTING:
            ctrl.update((0.0, 0.0, 0.0), 0.016)

        self.assertEqual(ctrl.state, WebLineState.ATTACHED)
        self.assertIsNotNone(ctrl.rope)

    def test_web_controller_miss_path(self):
        ctrl = WebController()
        target = AttachmentTarget(position=(0.0, 1.0, 0.0), confidence=0.1) # Low confidence -> Miss!

        ctrl.shoot((0.0, 0.0, 0.0), target)
        self.assertEqual(ctrl.state, WebLineState.SHOOTING)

        # Advance until projectile arrives at target
        while ctrl.state == WebLineState.SHOOTING:
            ctrl.update((0.0, 0.0, 0.0), 0.016)

        self.assertEqual(ctrl.state, WebLineState.MISSED)

        # Advance miss timer (0.15s) -> Transitions to RETRACTING
        for _ in range(12):
            ctrl.update((0.0, 0.0, 0.0), 0.016)

        self.assertEqual(ctrl.state, WebLineState.RETRACTING)

    def test_spider_module_determinism_and_requests(self):
        mod = SpiderModule({})
        mod.initialize()
        hand = create_mock_spider_hand()

        # Step 1: Process input
        mod.process_input({"Right": hand})
        mod.update(0.016)

        # Verify Audio Request emitted for shooting
        audio_reqs = mod.get_audio_requests()
        self.assertEqual(len(audio_reqs), 1)
        self.assertEqual(audio_reqs[0].sound_id, "web_shoot")

        # Verify Render Requests emitted for projectile
        render_reqs = mod.get_render_requests()
        effect_types = [req.effect_type for req in render_reqs]
        self.assertIn(EffectType.WEB_PROJECTILE, effect_types)
        self.assertIn(EffectType.WEB_RETICLE, effect_types)

if __name__ == "__main__":
    unittest.main()
