from enum import IntEnum
from typing import Dict, Any, List, Optional
import numpy as np

from src.modules.base_module import HeroModule, ModuleState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest, EffectType, CameraRequest
from src.engine.audio.types import AudioCategory
from src.engine.procedural.lightning import LightningGenerator

class ThunderState(IntEnum):
    """Explicit state machine states for thunder charging, strike, and failure paths."""
    IDLE = 0
    CHARGING = 1
    SUMMONED = 2
    DISCHARGING = 3
    COOLDOWN = 4
    INTERRUPTED = 5

class ThunderModule(HeroModule):
    """Thunder Engine module providing procedural fractal branching lightning, camera impulses, and eye aura overlays."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.state_machine = ThunderState.IDLE
        self.generator = LightningGenerator()
        
        self.charge_level = 0.0
        self.charge_rate = 1.2
        self.discharge_timer = 0.0
        self.cooldown_timer = 0.0
        self.interrupted_timer = 0.0
        self.seed = 1337

        self.hand_positions: List[Tuple[float, float, float]] = []
        self.camera_requests: List[CameraRequest] = []
        self.prev_state = ThunderState.IDLE

    @property
    def name(self) -> str:
        return "thunder"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Thunder Engine Procedural Lightning & Camera Impulses"

    def initialize(self) -> None:
        self.state = ModuleState.INITIALIZED

    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Process active hands detecting raised closed fist gestures."""
        self.hand_positions.clear()
        raised_fist_count = 0

        for hand in active_hands.values():
            if hand is not None:
                self.hand_positions.append(hand.get_centroid_ndc())
                if hand.gesture in ("RAISED_CLOSED_FIST", "Closed Fist"):
                    if hand.get_centroid_ndc()[1] > 0.1: # Raised high in NDC
                        raised_fist_count += 1

        is_charging_pose = raised_fist_count > 0

        if is_charging_pose:
            if self.state_machine in (ThunderState.IDLE, ThunderState.COOLDOWN):
                self.state_machine = ThunderState.CHARGING
        else:
            if self.state_machine == ThunderState.CHARGING:
                self.state_machine = ThunderState.INTERRUPTED
                self.interrupted_timer = 0.2
            elif self.state_machine == ThunderState.SUMMONED:
                self.state_machine = ThunderState.DISCHARGING
                self.discharge_timer = 0.35

    def update(self, dt: float) -> None:
        """Update state machine timers, charge levels, and camera impulses."""
        self.camera_requests.clear()
        self.seed += 1 # Advance seed for animated plasma jitter

        if self.state_machine == ThunderState.CHARGING:
            self.charge_level = min(1.0, self.charge_level + dt * self.charge_rate)
            if self.charge_level >= 1.0:
                self.state_machine = ThunderState.SUMMONED

        elif self.state_machine == ThunderState.INTERRUPTED:
            self.interrupted_timer -= dt
            self.charge_level = max(0.0, self.charge_level - dt * 2.0)
            if self.interrupted_timer <= 0.0:
                self.state_machine = ThunderState.COOLDOWN
                self.cooldown_timer = 0.3

        elif self.state_machine == ThunderState.DISCHARGING:
            self.discharge_timer -= dt
            # Trigger Camera Impulse Shake Request
            self.camera_requests.append(CameraRequest(
                "shake", intensity=0.08 * self.charge_level, duration=0.45, frequency=30.0
            ))

            if self.discharge_timer <= 0.0:
                self.state_machine = ThunderState.COOLDOWN
                self.cooldown_timer = 0.5
                self.charge_level = 0.0

        elif self.state_machine == ThunderState.COOLDOWN:
            self.cooldown_timer -= dt
            self.charge_level = max(0.0, self.charge_level - dt * 2.0)
            if self.cooldown_timer <= 0.0:
                self.state_machine = ThunderState.IDLE

        # Audio Lifecycle Management
        if self.prev_state != self.state_machine:
            if self.state_machine == ThunderState.CHARGING:
                self.emit_sound("thunder_charge", volume=0.8, category=AudioCategory.SFX)
            elif self.state_machine == ThunderState.DISCHARGING:
                self.emit_sound("thunder_strike", volume=1.0, category=AudioCategory.SFX)
            
            self.prev_state = self.state_machine

    def get_camera_requests(self) -> List[CameraRequest]:
        """Harvest camera/viewport manipulation requests."""
        return list(self.camera_requests)

    def get_render_requests(self) -> List[EffectRequest]:
        """Harvest composable rendering commands for procedural lightning and eye aura overlays."""
        requests: List[EffectRequest] = []

        # 1. Facial Eye Aura Primitive
        if self.charge_level > 0.05:
            requests.append(EffectRequest(
                EffectType.EYE_AURA,
                center=(0.0, 0.2), # Eye center position
                radius=0.12 * self.charge_level,
                color=(0.3, 0.85, 1.0),
                charge=self.charge_level
            ))

        # 2. Procedural Branching Lightning Polylines
        if self.state_machine in (ThunderState.CHARGING, ThunderState.SUMMONED, ThunderState.DISCHARGING):
            sky_start = (0.0, 1.1, 0.0)
            targets = self.hand_positions if self.hand_positions else [(0.0, -0.3, 0.0)]

            for i, target_pos in enumerate(targets):
                branches = self.generator.generate(
                    start=sky_start,
                    end=target_pos,
                    seed=self.seed + i * 100,
                    generations=5,
                    offset_scale=0.18,
                    branch_probability=0.35
                )

                for branch in branches:
                    points_2d = [(p[0], p[1]) for p in branch]
                    requests.append(EffectRequest(
                        EffectType.POLYLINE,
                        points=points_2d,
                        color=(0.6, 0.9, 1.0),
                        tension=self.charge_level,
                        thickness=1.5 if self.state_machine == ThunderState.DISCHARGING else 1.0
                    ))

        return requests

    def release(self) -> None:
        super().release()
