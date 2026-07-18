import sys
import threading
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.engine.utils.logger import setup_logger
from src.engine.audio.types import SoundHandle

logger = setup_logger("AudioBackend")

class SoundBackend(ABC):
    """Abstract interface for audio playback backends."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the underlying audio driver/hardware is available."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initializes backend hardware/software context."""
        pass

    @abstractmethod
    def load_sound(self, sound_id: str, file_path: str) -> bool:
        """Preloads a sound asset into memory."""
        pass

    @abstractmethod
    def play_sound(self, sound_id: str, volume: float = 1.0, loop: bool = False) -> Optional[SoundHandle]:
        """Triggers sound playback, returning a unique handle."""
        pass

    @abstractmethod
    def stop_sound(self, handle: SoundHandle) -> None:
        """Stops active sound playback associated with a handle."""
        pass

    @abstractmethod
    def stop_all(self) -> None:
        """Stops all currently playing sounds across all channels."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pauses all active audio playback."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resumes paused audio playback."""
        pass

    @abstractmethod
    def set_master_volume(self, volume: float) -> None:
        """Sets global master volume (0.0 to 1.0)."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases backend resources cleanly."""
        pass


class NullSoundBackend(SoundBackend):
    """Silent no-op backend for headless execution and unit tests."""

    def __init__(self):
        self.master_volume = 1.0
        self.loaded_sounds: Dict[str, str] = {}
        self.active_handles: Dict[SoundHandle, str] = {}

    def is_available(self) -> bool:
        return True

    def initialize(self) -> bool:
        logger.info("Initialized NullSoundBackend (silent mode).")
        return True

    def load_sound(self, sound_id: str, file_path: str) -> bool:
        self.loaded_sounds[sound_id] = file_path
        return True

    def play_sound(self, sound_id: str, volume: float = 1.0, loop: bool = False) -> Optional[SoundHandle]:
        handle = f"null_snd_{uuid.uuid4().hex[:8]}"
        self.active_handles[handle] = sound_id
        return handle

    def stop_sound(self, handle: SoundHandle) -> None:
        self.active_handles.pop(handle, None)

    def stop_all(self) -> None:
        self.active_handles.clear()

    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def release(self) -> None:
        self.loaded_sounds.clear()
        self.active_handles.clear()
        logger.info("NullSoundBackend released.")


class WinsoundBackend(SoundBackend):
    """Windows native winsound backend executing playback on background threads."""

    def __init__(self):
        self.master_volume = 1.0
        self.loaded_sounds: Dict[str, str] = {}
        self.active_threads: Dict[SoundHandle, threading.Thread] = {}

    def is_available(self) -> bool:
        return sys.platform == "win32"

    def initialize(self) -> bool:
        if not self.is_available():
            return False
        logger.info("Initialized WinsoundBackend.")
        return True

    def load_sound(self, sound_id: str, file_path: str) -> bool:
        self.loaded_sounds[sound_id] = file_path
        return True

    def play_sound(self, sound_id: str, volume: float = 1.0, loop: bool = False) -> Optional[SoundHandle]:
        file_path = self.loaded_sounds.get(sound_id)
        if not file_path:
            return None

        handle = f"win_snd_{uuid.uuid4().hex[:8]}"
        
        def _play_worker():
            try:
                import winsound
                flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
                if loop:
                    flags |= winsound.SND_LOOP | winsound.SND_ASYNC
                winsound.PlaySound(file_path, flags)
            except Exception as e:
                logger.error(f"Winsound playback error for {sound_id}: {e}")

        t = threading.Thread(target=_play_worker, daemon=True)
        t.start()
        self.active_threads[handle] = t
        return handle

    def stop_sound(self, handle: SoundHandle) -> None:
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        self.active_threads.pop(handle, None)

    def stop_all(self) -> None:
        self.stop_sound("")

    def pause(self) -> None:
        self.stop_all()

    def resume(self) -> None:
        pass

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def release(self) -> None:
        self.stop_all()
        self.loaded_sounds.clear()
        self.active_threads.clear()
        logger.info("WinsoundBackend released.")


class PygameBackend(SoundBackend):
    """Pygame mixer backend with multi-channel polyphonic sound support."""

    def __init__(self):
        self._initialized = False
        self.master_volume = 1.0
        self.loaded_sounds: Dict[str, Any] = {}
        self.active_channels: Dict[SoundHandle, Any] = {}

    def is_available(self) -> bool:
        try:
            import pygame
            return True
        except ImportError:
            return False

    def initialize(self) -> bool:
        if not self.is_available():
            return False
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
            logger.info("Initialized PygameBackend successfully.")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize PygameBackend: {e}")
            self._initialized = False
            return False

    def load_sound(self, sound_id: str, file_path: str) -> bool:
        if not self._initialized:
            return False
        try:
            import pygame
            sound_obj = pygame.mixer.Sound(file_path)
            self.loaded_sounds[sound_id] = sound_obj
            return True
        except Exception as e:
            logger.error(f"Pygame failed to load sound {sound_id} from {file_path}: {e}")
            return False

    def play_sound(self, sound_id: str, volume: float = 1.0, loop: bool = False) -> Optional[SoundHandle]:
        sound_obj = self.loaded_sounds.get(sound_id)
        if not sound_obj or not self._initialized:
            return None

        try:
            import pygame
            channel = pygame.mixer.find_channel()
            if channel:
                final_vol = max(0.0, min(1.0, volume * self.master_volume))
                sound_obj.set_volume(final_vol)
                loops = -1 if loop else 0
                channel.play(sound_obj, loops=loops)
                
                handle = f"pg_snd_{uuid.uuid4().hex[:8]}"
                self.active_channels[handle] = channel
                return handle
        except Exception as e:
            logger.error(f"Pygame play_sound error for {sound_id}: {e}")
        return None

    def stop_sound(self, handle: SoundHandle) -> None:
        channel = self.active_channels.pop(handle, None)
        if channel:
            try:
                channel.stop()
            except Exception:
                pass

    def stop_all(self) -> None:
        if self._initialized:
            try:
                import pygame
                pygame.mixer.stop()
            except Exception:
                pass
        self.active_channels.clear()

    def pause(self) -> None:
        if self._initialized:
            try:
                import pygame
                pygame.mixer.pause()
            except Exception:
                pass

    def resume(self) -> None:
        if self._initialized:
            try:
                import pygame
                pygame.mixer.unpause()
            except Exception:
                pass

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))

    def release(self) -> None:
        self.stop_all()
        self.loaded_sounds.clear()
        if self._initialized:
            try:
                import pygame
                pygame.mixer.quit()
            except Exception:
                pass
            self._initialized = False
        logger.info("PygameBackend released.")


class SoundBackendFactory:
    """Factory for constructing sound backends with explicit or automatic selection."""

    @staticmethod
    def create_backend(backend_type: str = "auto") -> SoundBackend:
        backend_type = backend_type.lower()
        logger.info(f"Creating sound backend (requested: '{backend_type}')...")

        if backend_type == "pygame":
            backend = PygameBackend()
            if backend.initialize():
                return backend
            logger.warning("Requested 'pygame' backend unavailable. Falling back to NullSoundBackend.")
            return NullSoundBackend()

        if backend_type == "winsound":
            backend = WinsoundBackend()
            if backend.initialize():
                return backend
            logger.warning("Requested 'winsound' backend unavailable. Falling back to NullSoundBackend.")
            return NullSoundBackend()

        if backend_type == "null":
            backend = NullSoundBackend()
            backend.initialize()
            return backend

        # Auto fallback order: Pygame -> Winsound -> Null
        pg_backend = PygameBackend()
        if pg_backend.initialize():
            return pg_backend

        win_backend = WinsoundBackend()
        if win_backend.initialize():
            return win_backend

        null_backend = NullSoundBackend()
        null_backend.initialize()
        return null_backend
