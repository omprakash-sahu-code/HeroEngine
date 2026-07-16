import random
import numpy as np
from typing import List, Dict, Any, Tuple

class Particle:
    """Represents a single visual spark/glowing point in NDC space."""

    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[float, float, float], lifespan: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color  # (r, g, b)
        self.lifespan = lifespan  # Initial duration in seconds
        self.remaining_life = lifespan  # Current duration in seconds

    def update(self, dt: float) -> bool:
        """Move particle, apply physics (drag/gravity), and tick down lifespan.

        Returns:
            bool: True if particle is still alive, False if dead.
        """
        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Apply light gravity/rising force (e.g. rising smoke/spark effect)
        self.vy += 0.05 * dt
        
        # Apply air resistance drag
        self.vx *= (1.0 - 0.5 * dt)
        self.vy *= (1.0 - 0.5 * dt)
        
        # Decrement life
        self.remaining_life -= dt
        return self.remaining_life > 0.0


class ParticleEmitter:
    """Manages spawning, updating, and exporting collections of active particles."""

    def __init__(self, limit: int = 2000):
        self.limit = limit
        self.particles: List[Particle] = []

    def emit(self, x: float, y: float, count: int, color: Tuple[float, float, float] = (1.0, 0.5, 0.1), speed: float = 0.6) -> None:
        """Spawn new particles at target coordinates with randomized velocities.

        Args:
            x, y: Spawning coordinates in NDC space.
            count: Number of particles to spawn.
            color: RGB color tuple.
            speed: Maximum velocity scale.
        """
        for _ in range(count):
            if len(self.particles) >= self.limit:
                break
                
            # Random radial velocity
            angle = random.uniform(0, 2 * np.pi)
            r_speed = random.uniform(0.05, speed)
            vx = r_speed * np.cos(angle)
            vy = r_speed * np.sin(angle)
            
            # Random lifespan
            lifespan = random.uniform(0.3, 0.8)
            
            self.particles.append(Particle(x, y, vx, vy, color, lifespan))

    def update(self, dt: float) -> None:
        """Advance simulation ticks for all active particles, removing dead ones."""
        # Update and filter alive particles
        self.particles = [p for p in self.particles if p.update(dt)]

    def get_render_data(self) -> Tuple[np.ndarray, int]:
        """Export particle positions, colors, and alpha values formatted for ModernGL upload.

        Returns:
            Tuple[np.ndarray, int]: Float32 numpy array with [x, y, r, g, b, a] per particle
                                    and total active particle count.
        """
        count = len(self.particles)
        if count == 0:
            return np.empty(0, dtype='f4'), 0

        data = []
        for p in self.particles:
            # Alpha decays linearly with remaining lifespan
            alpha = max(0.0, p.remaining_life / p.lifespan)
            data.extend([p.x, p.y, p.color[0], p.color[1], p.color[2], alpha])

        return np.array(data, dtype='f4'), count

    def clear(self) -> None:
        """Wipes all active particles."""
        self.particles.clear()
