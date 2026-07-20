import numpy as np
from typing import List, Tuple

class LightningGenerator:
    """Renderer-agnostic procedural geometry generator for fractal branching lightning arcs."""

    def __init__(self, default_generations: int = 5, default_offset_scale: float = 0.15, default_branch_prob: float = 0.35):
        self.default_generations = default_generations
        self.default_offset_scale = default_offset_scale
        self.default_branch_prob = default_branch_prob

    def generate(self, start: Tuple[float, float, float], end: Tuple[float, float, float],
                 seed: int = 42, generations: int = 5, offset_scale: float = 0.15,
                 branch_probability: float = 0.35) -> List[List[Tuple[float, float, float]]]:
        """Generates multi-segment branching polyline point streams using recursive midpoint displacement.

        Args:
            start: Starting 3D coordinates.
            end: Target 3D coordinates.
            seed: Seed for deterministic RNG.
            generations: Recursion depth (max midpoint splits).
            offset_scale: Initial displacement amplitude.
            branch_probability: Chance to spawn a secondary branch fork at midpoints.

        Returns:
            List[List[Tuple[float, float, float]]]: List of connected polyline branches.
        """
        rng = np.random.RandomState(seed)
        start_pt = np.array(start, dtype=np.float64)
        end_pt = np.array(end, dtype=np.float64)

        # Segments list: (p1, p2, is_main)
        segments = [(start_pt, end_pt, True)]
        secondary_branches: List[List[Tuple[float, float, float]]] = []

        for gen in range(generations):
            new_segments = []
            cur_offset = offset_scale / (1.8 ** gen)

            for p1, p2, is_main in segments:
                vec = p2 - p1
                dist = np.linalg.norm(vec)
                if dist < 1e-5:
                    new_segments.append((p1, p2, is_main))
                    continue

                dir_norm = vec / dist

                # Generate random perpendicular offset vector
                rand_vec = rng.uniform(-1.0, 1.0, size=3)
                perp = rand_vec - np.dot(rand_vec, dir_norm) * dir_norm
                perp_norm = np.linalg.norm(perp)
                if perp_norm > 1e-5:
                    perp /= perp_norm

                mid = (p1 + p2) * 0.5 + perp * rng.uniform(-cur_offset, cur_offset)

                new_segments.append((p1, mid, is_main))
                new_segments.append((mid, p2, is_main))

                # Secondary branch fork generation
                if is_main and rng.rand() < branch_probability and gen < generations - 1:
                    branch_dir = dir_norm + perp * rng.uniform(0.5, 1.2)
                    branch_dir /= max(1e-5, np.linalg.norm(branch_dir))
                    branch_len = dist * rng.uniform(0.3, 0.6)
                    branch_end = mid + branch_dir * branch_len
                    
                    # Generate small sub-branch polyline
                    sec_branch = [tuple(mid), tuple(branch_end)]
                    secondary_branches.append(sec_branch)

            segments = new_segments

        # Assemble main trunk polyline
        main_trunk: List[Tuple[float, float, float]] = [tuple(segments[0][0])]
        for p1, p2, is_main in segments:
            if is_main:
                main_trunk.append(tuple(p2))

        all_branches: List[List[Tuple[float, float, float]]] = [main_trunk] + secondary_branches
        return all_branches
