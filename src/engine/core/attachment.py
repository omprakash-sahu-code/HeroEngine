from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class AttachmentTarget:
    """Immutable data structure representing a physical attachment or anchor target."""
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    confidence: float = 1.0
    movable: bool = False
