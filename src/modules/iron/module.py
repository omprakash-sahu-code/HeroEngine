from enum import IntEnum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from src.modules.base_module import HeroModule, ModuleState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest, EffectType
from src.engine.audio.types import AudioCategory, PlaybackMode
from src.engine.core.target_detector import TargetDetector, TargetState

class IronState(IntEnum):
    """Explicit state machine states for repulsor energy weapons."""
    IDLE = 0
    CHARGING = 1
    CHARGED = 2
    FIRING = 3
    COOLDOWN = 4

class RepulsorHand:
    """Tracks state machine, charge levels, and targeting parameters per hand."""

    def __init__(self, label: str, charge_duration: float = 1.0, cooldown_duration: float = 0.5):
        self.label = label
        self.state = IronState.IDLE
        self.charge_level = 0.0  # 0.0 to 1.0
        self.charge_duration = charge_duration
        self.cooldown_duration = cooldown_duration
        
        self.cooldown_timer = 0.0
        self.firing_timer = 0.0
        self.firing_duration = 0.35
        
        self.palm_forward = False
        self.hand_state: Optional[HandState] = None
        self.target_state = TargetState(position=(0.0, 0.0, 0.0), locked=False, confidence=0.0)

class IronModule(HeroModule):
    """Iron Engine superhero module providing repulsor beam weapons and glassmorphism HUD."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.hands_data: Dict[str, RepulsorHand] = {
            "Left": RepulsorHand("Left"),
            "Right": RepulsorHand("Right")
        }
        self.target_detector = TargetDetector(lock_threshold=0.8)

    @property
    def name(self) -> str:
        return "iron"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Iron Engine Repulsor Weapons & High-Tech HUD"

    def initialize(self) -> None:
        self.state = ModuleState.INITIALIZED

    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Process active hands, updating targeting and palm pose state."""
        for label in ["Left", "Right"]:
            r_hand = self.hands_data[label]
            hand = active_hands.get(label)
            r_hand.hand_state = hand
            
            # Update target detector state
            r_hand.target_state = self.target_detector.evaluate_target(hand)
            
            if hand is not None:
                # Generic pose: Open Palm facing camera with index tip above wrist
                # In MediaPipe space, Y goes down, so tip Y < wrist Y
                is_palm_up = hand.landmarks[8][1] < hand.landmarks[0][1]
                r_hand.palm_forward = (hand.gesture == "Open Palm" and is_palm_up)
            else:
                r_hand.palm_forward = False

    def update(self, dt: float) -> None:
        """Advances state machine, time-based charging, pose loss decay, and audio emission."""
        for r_hand in self.hands_data.values():
            if r_hand.state == IronState.IDLE:
                if r_hand.palm_forward:
                    r_hand.state = IronState.CHARGING
                    r_hand.charge_level = min(1.0, r_hand.charge_level + dt / r_hand.charge_duration)
                    if r_hand.charge_level >= 1.0:
                        r_hand.state = IronState.CHARGED
                        self.emit_sound("hud_lock", volume=0.8, category=AudioCategory.UI)
                    else:
                        self.emit_sound("repulsor_charge", volume=0.7, category=AudioCategory.SFX)

            elif r_hand.state == IronState.CHARGING:
                if r_hand.palm_forward:
                    # Time-based charge accumulation (deterministic frame-rate independence)
                    r_hand.charge_level = min(1.0, r_hand.charge_level + dt / r_hand.charge_duration)
                    if r_hand.charge_level >= 1.0:
                        r_hand.state = IronState.CHARGED
                        self.emit_sound("hud_lock", volume=0.8, category=AudioCategory.UI)
                else:
                    # Pose-loss decay
                    r_hand.charge_level = max(0.0, r_hand.charge_level - dt * 2.0)
                    if r_hand.charge_level <= 0.0:
                        r_hand.state = IronState.IDLE

            elif r_hand.state == IronState.CHARGED:
                if r_hand.palm_forward:
                    # Check for trigger push velocity or full lock
                    speed = np.linalg.norm(r_hand.hand_state.velocity) if r_hand.hand_state else 0.0
                    # Trigger blast if pushed forward or fully charged lock
                    if speed > 0.5 or (r_hand.hand_state and r_hand.hand_state.pinch_distance < 0.1):
                        r_hand.state = IronState.FIRING
                        r_hand.firing_timer = r_hand.firing_duration
                        self.emit_sound("repulsor_fire", volume=1.0, category=AudioCategory.SFX)
                else:
                    # Pose loss decay from charged state
                    r_hand.charge_level = max(0.0, r_hand.charge_level - dt * 2.0)
                    if r_hand.charge_level <= 0.0:
                        r_hand.state = IronState.IDLE

            elif r_hand.state == IronState.FIRING:
                r_hand.firing_timer -= dt
                if r_hand.firing_timer <= 0.0:
                    r_hand.state = IronState.COOLDOWN
                    r_hand.cooldown_timer = r_hand.cooldown_duration
                    r_hand.charge_level = 0.0

            elif r_hand.state == IronState.COOLDOWN:
                r_hand.cooldown_timer -= dt
                if r_hand.cooldown_timer <= 0.0:
                    r_hand.state = IronState.IDLE

    def get_render_requests(self) -> List[EffectRequest]:
        """Harvest composable rendering commands for HUD reticles, charge rings, and repulsor beams."""
        requests: List[EffectRequest] = []
        
        for r_hand in self.hands_data.values():
            if r_hand.hand_state is None:
                continue

            pos_ndc = r_hand.hand_state.get_centroid_ndc()
            center_2d = (pos_ndc[0], pos_ndc[1])

            # 1. Composable HUD Target Reticle
            requests.append(EffectRequest(
                EffectType.HUD_TARGET,
                center=center_2d,
                radius=0.18,
                color=(0.1, 0.95, 1.0),
                locked=r_hand.target_state.locked
            ))

            # 2. Composable Repulsor Charging Ring
            if r_hand.state in (IronState.CHARGING, IronState.CHARGED):
                requests.append(EffectRequest(
                    EffectType.REPULSOR_RING,
                    center=center_2d,
                    radius=0.22,
                    color=(0.2, 0.85, 1.0),
                    charge=r_hand.charge_level
                ))

            # 3. Composable Repulsor Beam & Flash
            elif r_hand.state == IronState.FIRING:
                # Target endpoint towards top/center of screen
                beam_end = (center_2d[0] * 0.2, 0.9)
                
                requests.append(EffectRequest(
                    EffectType.REPULSOR_BEAM,
                    center=center_2d,
                    beam_end=beam_end,
                    radius=0.3,
                    color=(0.3, 0.9, 1.0),
                    charge=1.0
                ))
                
                requests.append(EffectRequest(
                    EffectType.REPULSOR_FLASH,
                    center=center_2d,
                    radius=0.25,
                    color=(1.0, 1.0, 1.0)
                ))
                
                # Emit particle burst
                requests.append(EffectRequest(
                    EffectType.PARTICLES,
                    center=center_2d,
                    count=30,
                    color=(0.2, 0.85, 1.0),
                    speed=1.2
                ))

        return requests

    def release(self) -> None:
        super().release()
