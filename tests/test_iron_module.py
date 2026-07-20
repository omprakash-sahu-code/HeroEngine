import unittest
from src.modules.iron.module import IronModule, IronState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectType
from src.engine.core.target_detector import TargetDetector, TargetState

def create_mock_palm_hand(label: str = "Right", push_speed: float = 0.0) -> HandState:
    """Creates a mock HandState representing a PALM_FORWARD posture."""
    landmarks = [(0.5, 0.5, 0.0)] * 21
    # Wrist at (0.5, 0.8, 0.0), Index tip at (0.5, 0.2, 0.0) -> Y goes down in MediaPipe
    landmarks[0] = (0.5, 0.8, 0.0)
    landmarks[8] = (0.5, 0.2, 0.0)
    landmarks[9] = (0.5, 0.6, 0.0)
    
    hand = HandState(label=label, score=0.95, landmarks=landmarks, gesture="Open Palm")
    hand.velocity = (0.0, -push_speed, 0.0)
    return hand

class TestIronModule(unittest.TestCase):
    """Test suite covering IronModule repulsor state machine, charge math, and target detector."""

    def test_target_detector_immutability(self):
        detector = TargetDetector(lock_threshold=0.8)
        hand = create_mock_palm_hand()
        target = detector.evaluate_target(hand)
        
        self.assertIsInstance(target, TargetState)
        self.assertTrue(target.locked)
        self.assertAlmostEqual(target.confidence, 0.95)
        
        with self.assertRaises(Exception):
            target.locked = False  # Immutable check

    def test_iron_state_machine_and_charge_math(self):
        mod = IronModule({})
        mod.initialize()
        r_hand = mod.hands_data["Right"]

        # Initial state IDLE
        self.assertEqual(r_hand.state, IronState.IDLE)
        self.assertEqual(r_hand.charge_level, 0.0)

        # Frame 1: Input PALM_FORWARD -> Transitions to CHARGING
        hand = create_mock_palm_hand()
        mod.process_input({"Right": hand})
        mod.update(0.1)

        self.assertEqual(r_hand.state, IronState.CHARGING)
        self.assertAlmostEqual(r_hand.charge_level, 0.1)

        # Check audio request emitted for charging
        audio_reqs = mod.get_audio_requests()
        self.assertEqual(len(audio_reqs), 1)
        self.assertEqual(audio_reqs[0].sound_id, "repulsor_charge")

        # Advance 1.0 seconds -> Reaches 100% charge and transitions to CHARGED
        mod.process_input({"Right": hand})
        mod.update(0.95)
        self.assertEqual(r_hand.state, IronState.CHARGED)
        self.assertAlmostEqual(r_hand.charge_level, 1.0)

    def test_pose_loss_charge_decay(self):
        mod = IronModule({})
        mod.initialize()
        r_hand = mod.hands_data["Right"]

        # Charge up to 0.5
        hand = create_mock_palm_hand()
        mod.process_input({"Right": hand})
        mod.update(0.5)
        self.assertEqual(r_hand.state, IronState.CHARGING)
        self.assertAlmostEqual(r_hand.charge_level, 0.5)

        # Lose PALM_FORWARD gesture
        mod.process_input({})
        mod.update(0.1)

        # Charge level decays and state resets to IDLE when charge hits 0
        self.assertLess(r_hand.charge_level, 0.5)
        mod.update(0.2)
        self.assertEqual(r_hand.charge_level, 0.0)
        self.assertEqual(r_hand.state, IronState.IDLE)

    def test_repulsor_firing_and_cooldown(self):
        mod = IronModule({})
        mod.initialize()
        r_hand = mod.hands_data["Right"]

        # Fully charge hand
        hand = create_mock_palm_hand()
        mod.process_input({"Right": hand})
        mod.update(1.0)
        self.assertEqual(r_hand.state, IronState.CHARGED)

        # Push forward (velocity > 0.5) -> Transitions to FIRING
        push_hand = create_mock_palm_hand(push_speed=1.0)
        mod.process_input({"Right": push_hand})
        mod.update(0.01)
        self.assertEqual(r_hand.state, IronState.FIRING)

        # Verify composable render requests (HUD_TARGET, REPULSOR_BEAM, REPULSOR_FLASH, PARTICLES)
        render_reqs = mod.get_render_requests()
        effect_types = [req.effect_type for req in render_reqs]
        self.assertIn(EffectType.HUD_TARGET, effect_types)
        self.assertIn(EffectType.REPULSOR_BEAM, effect_types)
        self.assertIn(EffectType.REPULSOR_FLASH, effect_types)

        # Advance past firing duration (0.35s) -> Transitions to COOLDOWN
        mod.process_input({"Right": push_hand})
        mod.update(0.4)
        self.assertEqual(r_hand.state, IronState.COOLDOWN)
        self.assertEqual(r_hand.charge_level, 0.0)

        # Cooldown enforcement: cannot charge or fire immediately
        mod.process_input({"Right": hand})
        mod.update(0.1)
        self.assertEqual(r_hand.state, IronState.COOLDOWN)

        # Advance past cooldown duration (0.5s) -> Returns to IDLE
        mod.update(0.45)
        self.assertEqual(r_hand.state, IronState.IDLE)

if __name__ == "__main__":
    unittest.main()
