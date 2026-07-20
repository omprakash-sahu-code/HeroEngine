import math
import numpy as np
from typing import List, Tuple

class WispGenerator:
    """Renderer-agnostic procedural geometry generator for swirling energy wisps."""

    def __init__(self, default_coils: float = 2.5, default_points: int = 30):
        self.default_coils = default_coils
        self.default_points = default_points

    def generate_swirl_wisp(self, center: Tuple[float, float, float], radius: float = 0.15,
                            seed: int = 42, num_points: int = 30, coils: float = 2.5,
                            time_offset: float = 0.0) -> List[Tuple[float, float, float]]:
        """Generates a parametric spiral polyline wisp stream around a target center.

        Args:
            center: 3D center point (x, y, z).
            radius: Outer spiral radius.
            seed: Seed for deterministic RNG.
            num_points: Number of points along polyline.
            coils: Number of full 360-degree rotations.
            time_offset: Dynamic phase shift for animated swirling.

        Returns:
            List[Tuple[float, float, float]]: 3D polyline point list.
        """
        rng = np.random.RandomState(seed)
        points: List[Tuple[float, float, float]] = []

        cx, cy, cz = center

        for i in range(num_points):
            t = i / max(1, num_points - 1)
            angle = t * coils * 2.0 * math.pi + time_offset

            # Archimedean tapering radius
            r = radius * (0.2 + 0.8 * (1.0 - t))
            jitter = rng.uniform(-0.06, 0.06) * radius

            px = cx + (r + jitter) * math.cos(angle)
            py = cy + (r + jitter) * math.sin(angle)
            pz = cz + (t - 0.5) * radius * 0.5

            points.append((px, py, pz))

        return points
