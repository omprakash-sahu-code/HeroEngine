from enum import IntEnum
from typing import Tuple, Optional, List
import numpy as np

from src.engine.physics.constraints import VerletRope
from src.engine.core.attachment import AttachmentTarget

class WebLineState(IntEnum):
    """Explicit state machine states for web-slinging mechanics."""
    IDLE = 0
    SHOOTING = 1
    ATTACHED = 2
    RETRACTING = 3
    SNAPPED = 4
    MISSED = 5

class WebController:
    """Manages web line state transitions, attachment targets, and Verlet physics rope simulation."""

    def __init__(self, segment_count: int = 20, max_tension_threshold: float = 0.5):
        self.state = WebLineState.IDLE
        self.segment_count = segment_count
        self.max_tension_threshold = max_tension_threshold
        
        self.rope: Optional[VerletRope] = None
        self.target: Optional[AttachmentTarget] = None
        self.origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.projectile_pos: np.ndarray = np.zeros(3, dtype=np.float64)
        
        self.projectile_speed = 8.0
        self.current_rope_len = 1.0
        self.retraction_rate = 1.5
        self.miss_timer = 0.0

    def shoot(self, origin: Tuple[float, float, float], target: Optional[AttachmentTarget]) -> None:
        """Triggers web projectile launch towards target anchor."""
        if self.state not in (WebLineState.IDLE, WebLineState.SNAPPED):
            return
        
        self.origin = origin
        self.projectile_pos = np.array(origin, dtype=np.float64)
        self.target = target
        self.state = WebLineState.SHOOTING

    def retract(self) -> None:
        """Initiates web line retraction."""
        if self.state == WebLineState.ATTACHED and self.rope:
            self.state = WebLineState.RETRACTING
            self.current_rope_len = self.rope.segment_len * self.rope.segment_count

    def update(self, origin: Tuple[float, float, float], dt: float) -> None:
        """Updates web state machine, projectile travel, and Verlet rope physics."""
        self.origin = origin

        if self.state == WebLineState.SHOOTING:
            target_pos = np.array(self.target.position if self.target else (origin[0], 1.2, origin[2]), dtype=np.float64)
            dir_vec = target_pos - self.projectile_pos
            dist = np.linalg.norm(dir_vec)

            if dist < 0.05:
                if self.target and self.target.confidence > 0.5:
                    self.state = WebLineState.ATTACHED
                    self.rope = VerletRope(origin, tuple(target_pos), segment_count=self.segment_count)
                    self.rope.attach_tail(tuple(target_pos))
                else:
                    self.state = WebLineState.MISSED
                    self.miss_timer = 0.15
            else:
                move_dir = dir_vec / max(1e-5, dist)
                self.projectile_pos += move_dir * min(dist, self.projectile_speed * dt)

        elif self.state == WebLineState.ATTACHED:
            if self.rope and self.target:
                self.rope.attach_head(origin)
                self.rope.attach_tail(self.target.position)
                self.rope.step(dt)

                # Check max tension snap
                if self.rope.get_tension() > self.max_tension_threshold:
                    self.state = WebLineState.SNAPPED
                    self.rope = None

        elif self.state == WebLineState.MISSED:
            self.miss_timer -= dt
            if self.miss_timer <= 0.0:
                self.state = WebLineState.RETRACTING
                self.current_rope_len = 0.5
                self.rope = VerletRope(origin, tuple(self.projectile_pos), segment_count=self.segment_count)

        elif self.state == WebLineState.RETRACTING:
            if self.rope:
                self.current_rope_len = max(0.05, self.current_rope_len - dt * self.retraction_rate)
                self.rope.attach_head(origin)
                self.rope.detach_tail()
                self.rope.set_rope_length(self.current_rope_len)
                self.rope.step(dt)

                if self.current_rope_len <= 0.05:
                    self.state = WebLineState.IDLE
                    self.rope = None
            else:
                self.state = WebLineState.IDLE

        elif self.state == WebLineState.SNAPPED:
            self.rope = None
            self.state = WebLineState.IDLE
