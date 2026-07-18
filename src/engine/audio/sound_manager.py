import os
import time
from typing import Dict, Any, List, Set, Optional

from src.engine.utils.logger import setup_logger
from src.engine.audio.types import AudioRequest, PlaybackMode, SoundHandle
from src.engine.audio.backend import SoundBackend, SoundBackendFactory

logger = setup_logger("SoundManager")

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac"}

class SoundManager:
    """Core sound management engine handling asset discovery, lazy loading, debouncing,

    single-log missing asset tracking, and backend playback orchestration.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        backend: Optional[SoundBackend] = None
    ):
        """Args:

            config: Configuration dictionary for audio subsystem settings.
            backend: Optional explicit SoundBackend implementation for dependency injection.
        """
        self.config = config or {}
        audio_cfg = self.config.get("audio", {})
        
        backend_type = audio_cfg.get("backend", "auto")
        self.master_volume = float(audio_cfg.get("volume", 1.0))
        
        self.backend = backend or SoundBackendFactory.create_backend(backend_type)
        self.backend.set_master_volume(self.master_volume)

        # Asset path index for lazy loading: sound_id -> file_path
        self._path_registry: Dict[str, str] = {}
        # Tracking loaded sounds in backend
        self._loaded_assets: Set[str] = set()
        # Single-log missing asset warning tracker
        self._logged_missing_assets: Set[str] = set()
        # Cooldown timestamps for debouncing: sound_id -> last_play_time
        self._cooldown_tracker: Dict[str, float] = {}

    def discover_sounds(self, directory: str) -> int:
        """Recursively scans a directory for sound files and indexes their paths lazily.

        Args:
            directory: Root directory path to scan.

        Returns:
            int: Number of new sound assets discovered.
        """
        if not os.path.exists(directory):
            return 0

        count = 0
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_AUDIO_EXTENSIONS:
                    sound_id = os.path.splitext(file)[0]
                    full_path = os.path.abspath(os.path.join(root, file))
                    if sound_id not in self._path_registry:
                        self._path_registry[sound_id] = full_path
                        count += 1
        
        if count > 0:
            logger.info(f"Discovered {count} sound assets in '{directory}'.")
        return count

    def register_sound(self, sound_id: str, file_path: str) -> bool:
        """Manually registers a sound asset path into the path index for lazy loading."""
        if os.path.exists(file_path):
            self._path_registry[sound_id] = os.path.abspath(file_path)
            return True
        return False

    def is_sound_registered(self, sound_id: str) -> bool:
        """Returns True if a sound asset is indexed in the path registry."""
        return sound_id in self._path_registry

    def process_requests(self, requests: List[AudioRequest]) -> List[SoundHandle]:
        """Processes a batch of frame AudioRequests from active hero modules or engine.

        Args:
            requests: List of AudioRequest dataclasses harvested for the current tick.

        Returns:
            List[SoundHandle]: Generated playback handles for triggered audio.
        """
        handles: List[SoundHandle] = []
        now = time.perf_counter()

        for req in requests:
            sound_id = req.sound_id

            # 1. Flexible cooldown debouncing check
            if req.cooldown_ms > 0:
                last_played = self._cooldown_tracker.get(sound_id, 0.0)
                if (now - last_played) < (req.cooldown_ms / 1000.0):
                    # Skip duplicate request within cooldown window
                    continue

            # 2. Check path registry & missing asset single logging
            if sound_id not in self._path_registry:
                if sound_id not in self._logged_missing_assets:
                    logger.warning(f"Missing sound asset: {sound_id}")
                    self._logged_missing_assets.add(sound_id)
                continue

            # 3. Lazy loading into backend on first playback
            if sound_id not in self._loaded_assets:
                file_path = self._path_registry[sound_id]
                loaded = self.backend.load_sound(sound_id, file_path)
                if loaded:
                    self._loaded_assets.add(sound_id)
                else:
                    logger.error(f"Failed to load sound asset into backend: {sound_id}")
                    continue

            # 4. Trigger sound playback via backend
            is_looping = req.playback_mode in (PlaybackMode.LOOP, PlaybackMode.UNTIL_STOPPED)
            handle = self.backend.play_sound(
                sound_id=sound_id,
                volume=req.volume,
                loop=is_looping
            )

            if handle:
                self._cooldown_tracker[sound_id] = now
                handles.append(handle)

        return handles

    def stop_handle(self, handle: SoundHandle) -> None:
        """Stops active sound playback associated with a handle."""
        self.backend.stop_sound(handle)

    def stop_all(self) -> None:
        """Stops all active audio playback across all channels."""
        self.backend.stop_all()

    def set_master_volume(self, volume: float) -> None:
        """Sets global master volume."""
        self.master_volume = max(0.0, min(1.0, volume))
        self.backend.set_master_volume(self.master_volume)

    def release(self) -> None:
        """Releases audio backend and clears cached path registries."""
        self.backend.release()
        self._path_registry.clear()
        self._loaded_assets.clear()
        self._logged_missing_assets.clear()
        self._cooldown_tracker.clear()
        logger.info("SoundManager released cleanly.")
