import math
from typing import Tuple

class CameraImpulse:
    """Decoupled camera/viewport translation impulse system for screen shake."""

    def __init__(self):
        self.intensity = 0.0
        self.duration = 0.0
        self.remaining_time = 0.0
        self.frequency = 25.0
        self.time_elapsed = 0.0

    def trigger_impulse(self, intensity: float = 0.05, duration: float = 0.4, frequency: float = 25.0) -> None:
        """Triggers a camera impulse shake event."""
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)
        self.remaining_time = self.duration
        self.frequency = frequency

    def update(self, dt: float) -> Tuple[float, float]:
        """Updates camera impulse decay and calculates (dx, dy) translation offset.

        Args:
            dt: Delta time in seconds.

        Returns:
            Tuple[float, float]: Current (dx, dy) screen translation offset.
        """
        if self.remaining_time <= 0.0:
            self.intensity = 0.0
            self.duration = 0.0
            return (0.0, 0.0)

        self.time_elapsed += dt
        self.remaining_time = max(0.0, self.remaining_time - dt)

        # Exponential decay factor (1.0 -> 0.0)
        decay_factor = (self.remaining_time / max(1e-5, self.duration)) ** 2
        current_amp = self.intensity * decay_factor

        # Damped multi-frequency noise offset
        dx = current_amp * math.sin(self.time_elapsed * self.frequency * 1.3)
        dy = current_amp * math.cos(self.time_elapsed * self.frequency * 0.9)

        return (dx, dy)
