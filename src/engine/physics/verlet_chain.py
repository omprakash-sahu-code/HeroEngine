import numpy as np
from typing import Tuple, List

class VerletChain:
    """A generic, reusable Verlet constraint chain for physics simulation.

    Useful for modeling whips, ropes, strings, tentacles, and webs.
    """

    def __init__(
        self,
        num_nodes: int = 15,
        link_distance: float = 0.04,
        gravity: Tuple[float, float] = (0.0, -0.35),
        damping: float = 0.95,
        initial_anchor: Tuple[float, float] = (0.0, 0.0)
    ):
        self.num_nodes = num_nodes
        self.link_distance = link_distance
        self.gravity = np.array(gravity, dtype='f4')
        self.damping = damping

        # Initialize all nodes at the starting anchor position to prevent elastic snaps
        self.positions = np.tile(initial_anchor, (num_nodes, 1)).astype('f4')
        self.prev_positions = np.copy(self.positions)

    def update(self, anchor_pos: Tuple[float, float], dt: float) -> None:
        """Advance the physics simulation by one tick.

        Args:
            anchor_pos: The NDC coordinates (x, y) where the head node is pinned.
            dt: Time step delta in seconds.
        """
        # Cap dt to avoid instabilities during lags
        dt = min(dt, 0.05)

        # 1. Update velocities and apply external forces (gravity)
        # Node 0 is anchored, so we only integrate nodes 1 to N-1
        for i in range(1, self.num_nodes):
            vel = (self.positions[i] - self.prev_positions[i]) * self.damping
            self.prev_positions[i] = np.copy(self.positions[i])
            self.positions[i] += vel + self.gravity * (dt ** 2)

        # 2. Pin head node to anchor position
        self.positions[0] = anchor_pos
        self.prev_positions[0] = anchor_pos

        # 3. Solve distance constraints iteratively (Verlet relaxation)
        # 8 iterations are usually sufficient for tight, stable rope constraints
        for _ in range(8):
            # Enforce head anchor lock
            self.positions[0] = anchor_pos

            for i in range(self.num_nodes - 1):
                p1 = self.positions[i]
                p2 = self.positions[i + 1]

                diff = p2 - p1
                dist = np.linalg.norm(diff)

                if dist > 1e-5:
                    difference = self.link_distance - dist
                    # Adjust nodes to restore original link distance
                    percent = (difference / dist) * 0.5
                    offset = diff * percent

                    if i > 0:
                        # Shared adjustment
                        self.positions[i] -= offset
                        self.positions[i + 1] += offset
                    else:
                        # Node 0 is pinned, so shift Node 1 by the full offset
                        self.positions[i + 1] += offset * 2.0
