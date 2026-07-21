from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class TelemetryFrame:
    """Transport-agnostic Data Transfer Object (DTO) containing standardized telemetry values."""
    timestamp: float
    frame_number: int
    hands: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    gestures: Dict[str, str] = field(default_factory=dict)
    module: Optional[str] = None
    camera: Optional[Dict[str, float]] = None
    effects: List[Dict[str, Any]] = field(default_factory=list)
    fps: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize frame payload to a clean dictionary structure."""
        return {
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "fps": round(self.fps, 1),
            "module": self.module,
            "hands": self.hands,
            "gestures": self.gestures,
            "camera": self.camera,
            "effects": self.effects
        }
