from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple

SoundHandle = str

class AudioCategory(Enum):
    """Categories for sound request categorization and independent volume control."""
    SFX = "sfx"
    UI = "ui"
    AMBIENT = "ambient"
    MUSIC = "music"
    VOICE = "voice"

class PlaybackMode(Enum):
    """Playback modes for audio execution."""
    ONCE = "once"
    LOOP = "loop"
    UNTIL_STOPPED = "until_stopped"

@dataclass(frozen=True)
class AudioRequest:
    """Immutable data request representing a sound playback command emitted by modules or engine core."""
    sound_id: str
    volume: float = 1.0
    playback_mode: PlaybackMode = PlaybackMode.ONCE
    category: AudioCategory = AudioCategory.SFX
    position: Optional[Tuple[float, float, float]] = None
    cooldown_ms: float = 0.0
    module_name: Optional[str] = None
    handle_id: Optional[str] = None

    def __post_init__(self):
        # Clamp volume between 0.0 and 1.0 for thread/safety guarantee
        clamped_vol = max(0.0, min(1.0, float(self.volume)))
        object.__setattr__(self, "volume", clamped_vol)
