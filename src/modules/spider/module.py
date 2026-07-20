from typing import Dict, Any, List, Optional
import numpy as np

from src.modules.base_module import HeroModule, ModuleState
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest, EffectType
from src.engine.audio.types import AudioCategory
from src.engine.core.attachment import AttachmentTarget
from src.modules.spider.web_controller import WebController, WebLineState

class SpiderModule(HeroModule):
    """Spider Engine module providing dynamic web-slinging with Verlet constraint rope physics."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.controllers: Dict[str, WebController] = {
            "Left": WebController(),
            "Right": WebController()
        }
        self.hand_states: Dict[str, Optional[HandState]] = {"Left": None, "Right": None}
        self.prev_states: Dict[str, WebLineState] = {"Left": WebLineState.IDLE, "Right": WebLineState.IDLE}

    @property
    def name(self) -> str:
        return "spider"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Spider Engine Web-Slinging & Constraint Physics"

    def initialize(self) -> None:
        self.state = ModuleState.INITIALIZED

    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Process active hands, detecting INDEX_PINKY_EXTENDED poses and shooting webs."""
        for label in ["Left", "Right"]:
            ctrl = self.controllers[label]
            hand = active_hands.get(label)
            self.hand_states[label] = hand

            if hand is not None:
                origin = hand.get_centroid_ndc()
                
                # Check generic INDEX_PINKY_EXTENDED pose
                is_web_pose = (hand.gesture == "INDEX_PINKY_EXTENDED")

                if is_web_pose:
                    if ctrl.state == WebLineState.IDLE:
                        # Target anchor default towards top screen boundary
                        target_pos = (origin[0] * 0.5, 0.9, 0.0)
                        target = AttachmentTarget(position=target_pos, confidence=0.9)
                        ctrl.shoot(origin, target)
                else:
                    if ctrl.state == WebLineState.ATTACHED:
                        ctrl.retract()

    def update(self, dt: float) -> None:
        """Updates physics simulations and emits audio lifecycle events."""
        for label in ["Left", "Right"]:
            ctrl = self.controllers[label]
            hand = self.hand_states[label]
            origin = hand.get_centroid_ndc() if hand else (0.0, 0.0, 0.0)
            
            prev_s = self.prev_states[label]
            ctrl.update(origin, dt)
            cur_s = ctrl.state

            # Audio Lifecycle Triggering
            if prev_s != cur_s:
                if cur_s == WebLineState.SHOOTING:
                    self.emit_sound("web_shoot", volume=0.8, category=AudioCategory.SFX)
                elif cur_s == WebLineState.ATTACHED:
                    self.emit_sound("web_attach", volume=0.9, category=AudioCategory.SFX)
                elif cur_s == WebLineState.SNAPPED:
                    self.emit_sound("web_snap", volume=1.0, category=AudioCategory.SFX)
                
                self.prev_states[label] = cur_s

    def get_render_requests(self) -> List[EffectRequest]:
        """Harvest composable rendering commands for polyline web lines, projectiles, and splatches."""
        requests: List[EffectRequest] = []

        for label in ["Left", "Right"]:
            ctrl = self.controllers[label]
            hand = self.hand_states[label]

            if hand is not None:
                origin_2d = (hand.get_centroid_ndc()[0], hand.get_centroid_ndc()[1])
                
                # 1. Targeting Crosshair Reticle
                requests.append(EffectRequest(
                    EffectType.WEB_RETICLE,
                    center=(origin_2d[0] * 0.5, 0.9),
                    radius=0.1
                ))

            # 2. Traveling Web Projectile
            if ctrl.state == WebLineState.SHOOTING:
                proj_2d = (ctrl.projectile_pos[0], ctrl.projectile_pos[1])
                orig_2d = (ctrl.origin[0], ctrl.origin[1])
                requests.append(EffectRequest(
                    EffectType.WEB_PROJECTILE,
                    start=orig_2d,
                    end=proj_2d,
                    color=(0.95, 0.95, 1.0)
                ))

            # 3. Polyline Web Line & Anchor Impact Splatch
            elif ctrl.state in (WebLineState.ATTACHED, WebLineState.RETRACTING) and ctrl.rope:
                rope_points = ctrl.rope.get_point_positions()
                points_2d = [(p[0], p[1]) for p in rope_points]
                tension = ctrl.rope.get_tension()

                requests.append(EffectRequest(
                    EffectType.POLYLINE,
                    points=points_2d,
                    color=(0.92, 0.95, 1.0),
                    tension=tension,
                    thickness=1.2
                ))

                if ctrl.state == WebLineState.ATTACHED and ctrl.target:
                    target_2d = (ctrl.target.position[0], ctrl.target.position[1])
                    requests.append(EffectRequest(
                        EffectType.WEB_SPLATCH,
                        center=target_2d,
                        radius=0.12,
                        color=(0.95, 0.95, 1.0)
                    ))

        return requests

    def release(self) -> None:
        super().release()
