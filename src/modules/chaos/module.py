from enum import IntEnum
from typing import Dict, Any, List, Tuple, Optional

from src.modules.base_module import HeroModule, ModuleState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest, EffectType
from src.engine.audio.types import AudioCategory
from src.engine.procedural.wisps import WispGenerator
from src.engine.physics.force_field import ForceField, FieldMode

class ChaosState(IntEnum):
    """Explicit state machine states for chaos energy manipulation and failure paths."""
    IDLE = 0
    CHARGING = 1
    MANIPULATING = 2
    RELEASING = 3
    COOLDOWN = 4
    INTERRUPTED = 5

class ChaosModule(HeroModule):
    """Chaos Engine module providing telekinetic force fields, swirl energy wisps, and screen distortion shaders."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.state_machine = ChaosState.IDLE
        self.wisp_gen = WispGenerator()
        self.force_field = ForceField()

        self.energy_level = 0.0
        self.charge_rate = 1.5
        self.release_timer = 0.0
        self.cooldown_timer = 0.0
        self.interrupted_timer = 0.0
        self.time_elapsed = 0.0
        self.seed = 42

        self.hand_positions: List[Tuple[float, float, float]] = []
        self.prev_state = ChaosState.IDLE

    @property
    def name(self) -> str:
        return "chaos"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Chaos Engine Telekinetic Manipulation & Screen Distortion"

    def initialize(self) -> None:
        self.state = ModuleState.INITIALIZED

    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Process active hands detecting CLAW_HAND gestures."""
        self.hand_positions.clear()
        claw_count = 0

        for hand in active_hands.values():
            if hand is not None:
                self.hand_positions.append(hand.get_centroid_ndc())
                if hand.gesture == "CLAW_HAND" or hand.pinch_distance < 0.35:
                    claw_count += 1

        is_claw_pose = claw_count > 0

        if is_claw_pose:
            if self.state_machine in (ChaosState.IDLE, ChaosState.COOLDOWN):
                self.state_machine = ChaosState.CHARGING
        else:
            if self.state_machine == ChaosState.CHARGING:
                self.state_machine = ChaosState.INTERRUPTED
                self.interrupted_timer = 0.2
            elif self.state_machine == ChaosState.MANIPULATING:
                self.state_machine = ChaosState.RELEASING
                self.release_timer = 0.35

    def update(self, dt: float) -> None:
        """Update force fields, energy levels, and state transitions."""
        self.time_elapsed += dt
        self.force_field.clear()

        # Update ForceField attractors
        for hand_pos in self.hand_positions:
            mode = FieldMode.REPULSE if self.state_machine == ChaosState.RELEASING else FieldMode.ATTRACT
            self.force_field.add_attractor(
                position=hand_pos,
                strength=3.0 * self.energy_level,
                radius=0.6,
                mode=mode
            )

        if self.state_machine == ChaosState.CHARGING:
            self.energy_level = min(1.0, self.energy_level + dt * self.charge_rate)
            if self.energy_level >= 1.0:
                self.state_machine = ChaosState.MANIPULATING

        elif self.state_machine == ChaosState.INTERRUPTED:
            self.interrupted_timer -= dt
            self.energy_level = max(0.0, self.energy_level - dt * 2.5)
            if self.interrupted_timer <= 0.0:
                self.state_machine = ChaosState.COOLDOWN
                self.cooldown_timer = 0.3

        elif self.state_machine == ChaosState.RELEASING:
            self.release_timer -= dt
            if self.release_timer <= 0.0:
                self.state_machine = ChaosState.COOLDOWN
                self.cooldown_timer = 0.4
                self.energy_level = 0.0

        elif self.state_machine == ChaosState.COOLDOWN:
            self.cooldown_timer -= dt
            self.energy_level = max(0.0, self.energy_level - dt * 2.0)
            if self.cooldown_timer <= 0.0:
                self.state_machine = ChaosState.IDLE

        # Audio Lifecycle Management
        if self.prev_state != self.state_machine:
            if self.state_machine == ChaosState.CHARGING:
                self.emit_sound("chaos_hum", volume=0.7, category=AudioCategory.SFX)
            elif self.state_machine == ChaosState.RELEASING:
                self.emit_sound("chaos_blast", volume=1.0, category=AudioCategory.SFX)
            
            self.prev_state = self.state_machine

    def get_render_requests(self) -> List[EffectRequest]:
        """Harvest composable rendering commands for swirl wisps and screen distortion fields."""
        requests: List[EffectRequest] = []

        if self.energy_level < 0.05:
            return requests

        targets = self.hand_positions if self.hand_positions else [(0.0, 0.0, 0.0)]

        for i, center_pos in enumerate(targets):
            # 1. Screen-Space UV Distortion Field Request
            requests.append(EffectRequest(
                EffectType.DISTORTION_FIELD,
                center=(center_pos[0], center_pos[1]),
                radius=0.4 * self.energy_level,
                color=(0.95, 0.1, 0.25),
                strength=self.energy_level * (2.0 if self.state_machine == ChaosState.RELEASING else 1.0)
            ))

            # 2. Procedural Swirling Energy Wisps
            for w in range(3):
                wisp_pts_3d = self.wisp_gen.generate_swirl_wisp(
                    center=center_pos,
                    radius=0.22 * self.energy_level,
                    seed=self.seed + i * 50 + w * 10,
                    num_points=25,
                    coils=2.2,
                    time_offset=self.time_elapsed * (4.0 + w * 2.0)
                )

                pts_2d = [(p[0], p[1]) for p in wisp_pts_3d]
                requests.append(EffectRequest(
                    EffectType.WISP_ARC,
                    points=pts_2d,
                    color=(1.0, 0.15 + w * 0.1, 0.3),
                    thickness=1.4 if self.state_machine == ChaosState.RELEASING else 1.0
                ))

            # 3. Particle Attraction / Blast Request
            requests.append(EffectRequest(
                "emit_particles",
                center=(center_pos[0], center_pos[1]),
                count=12 if self.state_machine == ChaosState.RELEASING else 3,
                color=(1.0, 0.1, 0.25),
                speed=0.9 if self.state_machine == ChaosState.RELEASING else 0.3,
                mode=0.0
            ))

        return requests

    def release(self) -> None:
        super().release()
