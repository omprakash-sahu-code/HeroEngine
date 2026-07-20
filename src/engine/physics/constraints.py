import numpy as np
from typing import List, Tuple, Optional

class PointMass:
    """Represents a physical point mass in a Verlet integration simulation."""

    def __init__(self, position: Tuple[float, float, float], mass: float = 1.0, pinned: bool = False):
        self.position = np.array(position, dtype=np.float64)
        self.old_position = np.array(position, dtype=np.float64)
        self.acceleration = np.zeros(3, dtype=np.float64)
        self.mass = mass
        self.pinned = pinned

    def update(self, dt: float, damping: float = 0.98) -> None:
        """Verlet integration step."""
        if self.pinned:
            return
        
        velocity = (self.position - self.old_position) * damping
        self.old_position = self.position.copy()
        self.position += velocity + self.acceleration * (dt ** 2)
        self.acceleration.fill(0.0)

    def apply_force(self, force: Tuple[float, float, float]) -> None:
        if not self.pinned and self.mass > 0.0:
            self.acceleration += np.array(force, dtype=np.float64) / self.mass

class DistanceConstraint:
    """Distance constraint enforcing fixed resting length between two point masses."""

    def __init__(self, p1: PointMass, p2: PointMass, rest_length: float, stiffness: float = 0.95):
        self.p1 = p1
        self.p2 = p2
        self.rest_length = rest_length
        self.stiffness = stiffness

    def solve(self) -> None:
        delta = self.p2.position - self.p1.position
        current_len = np.linalg.norm(delta)
        
        if current_len < 1e-7:
            return
        
        diff = (current_len - self.rest_length) / current_len
        correction = delta * 0.5 * diff * self.stiffness

        if not self.p1.pinned and not self.p2.pinned:
            self.p1.position += correction
            self.p2.position -= correction
        elif not self.p1.pinned:
            self.p1.position += correction * 2.0
        elif not self.p2.pinned:
            self.p2.position -= correction * 2.0

class VerletSolver:
    """Verlet integration physics solver maintaining point masses and distance constraints."""

    def __init__(self, damping: float = 0.98, iterations: int = 8):
        self.points: List[PointMass] = []
        self.constraints: List[DistanceConstraint] = []
        self.damping = damping
        self.iterations = iterations

    def step(self, dt: float, gravity: Tuple[float, float, float] = (0.0, -0.5, 0.0)) -> None:
        # 1. Apply gravity and integrate
        for p in self.points:
            p.apply_force(gravity)
            p.update(dt, damping=self.damping)

        # 2. Iterative constraint relaxation
        for _ in range(self.iterations):
            for c in self.constraints:
                c.solve()

class VerletRope(VerletSolver):
    """Generic physical rope solver composed of connected point masses and distance constraints."""

    def __init__(self, start_pos: Tuple[float, float, float], end_pos: Tuple[float, float, float],
                 segment_count: int = 20, stiffness: float = 0.95, damping: float = 0.98, iterations: int = 8):
        super().__init__(damping=damping, iterations=iterations)
        
        start = np.array(start_pos, dtype=np.float64)
        end = np.array(end_pos, dtype=np.float64)
        total_len = np.linalg.norm(end - start)
        self.segment_count = segment_count
        self.segment_len = total_len / max(1, segment_count)

        # Create points along segment line
        for i in range(segment_count + 1):
            t = i / float(segment_count)
            pos = start + (end - start) * t
            self.points.append(PointMass(tuple(pos), mass=1.0))

        # Pin start point
        self.points[0].pinned = True

        # Create adjacent distance constraints
        for i in range(segment_count):
            self.constraints.append(DistanceConstraint(
                self.points[i], self.points[i + 1], rest_length=self.segment_len, stiffness=stiffness
            ))

    def attach_head(self, pos: Tuple[float, float, float]) -> None:
        """Pins and moves origin head point to position."""
        self.points[0].position = np.array(pos, dtype=np.float64)
        self.points[0].old_position = self.points[0].position.copy()
        self.points[0].pinned = True

    def attach_tail(self, pos: Tuple[float, float, float]) -> None:
        """Pins and moves end tail point to position."""
        self.points[-1].position = np.array(pos, dtype=np.float64)
        self.points[-1].old_position = self.points[-1].position.copy()
        self.points[-1].pinned = True

    def detach_tail(self) -> None:
        """Unpins end tail point."""
        self.points[-1].pinned = False

    def get_tension(self) -> float:
        """Calculates average stretch ratio tension across rope constraints."""
        if not self.constraints:
            return 0.0
        
        total_stretch = 0.0
        for c in self.constraints:
            cur_len = np.linalg.norm(c.p2.position - c.p1.position)
            stretch = max(0.0, (cur_len - c.rest_length) / max(1e-5, c.rest_length))
            total_stretch += stretch
            
        return total_stretch / len(self.constraints)

    def set_rope_length(self, new_length: float) -> None:
        """Updates constraint rest lengths for dynamic web retraction or extension."""
        self.segment_len = max(0.01, new_length / float(self.segment_count))
        for c in self.constraints:
            c.rest_length = self.segment_len

    def get_point_positions(self) -> List[Tuple[float, float, float]]:
        """Returns current 3D coordinates of all rope points."""
        return [tuple(p.position) for p in self.points]
