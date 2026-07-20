from enum import Enum
import numpy as np
from typing import List, Tuple

class FieldMode(Enum):
    ATTRACT = 0
    REPULSE = 1
    VORTEX = 2

class FieldAttractor:
    """Represents a local force point in 3D space."""

    def __init__(self, position: Tuple[float, float, float], strength: float = 1.0,
                 radius: float = 0.5, mode: FieldMode = FieldMode.ATTRACT):
        self.position = position
        self.strength = strength
        self.radius = radius
        self.mode = mode

class ForceField:
    """Generic force field solver calculating attractor, repulsor, and vortex forces."""

    def __init__(self):
        self.attractors: List[FieldAttractor] = []

    def add_attractor(self, position: Tuple[float, float, float], strength: float = 1.0,
                      radius: float = 0.5, mode: FieldMode = FieldMode.ATTRACT) -> FieldAttractor:
        attractor = FieldAttractor(position, strength, radius, mode)
        self.attractors.append(attractor)
        return attractor

    def clear(self) -> None:
        self.attractors.clear()

    def compute_force(self, point: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Calculates net force vector acting on a target point.

        Args:
            point: 3D coordinates of target.

        Returns:
            Tuple[float, float, float]: Net (fx, fy, fz) force vector.
        """
        pt = np.array(point, dtype=np.float64)
        net_force = np.zeros(3, dtype=np.float64)

        for attractor in self.attractors:
            att_pos = np.array(attractor.position, dtype=np.float64)
            vec = att_pos - pt
            dist = np.linalg.norm(vec)

            if 1e-5 < dist < attractor.radius:
                dir_norm = vec / dist
                falloff = (1.0 - (dist / attractor.radius)) ** 2
                mag = attractor.strength * falloff

                if attractor.mode == FieldMode.ATTRACT:
                    net_force += dir_norm * mag
                elif attractor.mode == FieldMode.REPULSE:
                    net_force -= dir_norm * mag
                elif attractor.mode == FieldMode.VORTEX:
                    # Tangential force in 2D XY plane: (-dir_y, dir_x, 0)
                    tangent = np.array([-dir_norm[1], dir_norm[0], 0.0], dtype=np.float64)
                    net_force += tangent * mag

        return (float(net_force[0]), float(net_force[1]), float(net_force[2]))
