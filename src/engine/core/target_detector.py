from dataclasses import dataclass
from typing import Tuple, Optional, List
from src.engine.core.input_manager import HandState

@dataclass(frozen=True)
class TargetState:
    """Immutable data structure describing an acquired target."""
    position: Tuple[float, float, float]
    locked: bool
    confidence: float

class TargetDetector:
    """Decoupled target acquisition system evaluating hand positions and lock thresholds."""

    def __init__(self, lock_threshold: float = 0.8):
        self.lock_threshold = lock_threshold

    def evaluate_target(self, hand: Optional[HandState]) -> TargetState:
        """Evaluates hand position and returns an immutable TargetState.

        Args:
            hand: Active HandState or None.

        Returns:
            TargetState: Acquired targeting parameters.
        """
        if hand is None:
            return TargetState(position=(0.0, 0.0, 0.0), locked=False, confidence=0.0)

        # Convert NDC centroid
        pos = hand.get_centroid_ndc()
        locked = hand.score >= self.lock_threshold
        
        return TargetState(
            position=pos,
            locked=locked,
            confidence=hand.score
        )
