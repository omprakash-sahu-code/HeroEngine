import time

class DebounceTimer:
    """Timer helper that matches conditions over consecutive triggers or timestamps."""

    def __init__(self, required_duration: float):
        """Args:

            required_duration: Time in seconds the trigger must be active to succeed.
        """
        self.required_duration = required_duration
        self.start_time = None

    def update(self, condition: bool) -> bool:
        """Update timer state based on whether trigger condition is met.

        Args:
            condition: True if the raw event matches.

        Returns:
            bool: True if the condition has been met for the required duration.
        """
        if not condition:
            self.start_time = None
            return False
            
        if self.start_time is None:
            self.start_time = time.time()
            
        elapsed = time.time() - self.start_time
        return elapsed >= self.required_duration


class CooldownTracker:
    """Tracks ability activation cooldown times."""

    def __init__(self, cooldown_duration: float):
        """Args:

            cooldown_duration: Duration in seconds to lock trigger.
        """
        self.cooldown_duration = cooldown_duration
        self.last_activated_time = 0.0

    def trigger(self) -> bool:
        """Attempts to trigger the ability.

        Returns:
            bool: True if cooldown elapsed and trigger succeeded, False if blocked.
        """
        current_time = time.time()
        if current_time - self.last_activated_time >= self.cooldown_duration:
            self.last_activated_time = current_time
            return True
        return False

    def is_cooling_down(self) -> bool:
        """Check if currently cooling down.

        Returns:
            bool: True if cooldown in progress.
        """
        return (time.time() - self.last_activated_time) < self.cooldown_duration
