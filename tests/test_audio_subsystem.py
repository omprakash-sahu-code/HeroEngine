import os
import tempfile
import unittest
import time
from typing import List

from src.engine.audio.types import AudioRequest, AudioCategory, PlaybackMode
from src.engine.audio.backend import (
    NullSoundBackend,
    WinsoundBackend,
    PygameBackend,
    SoundBackendFactory
)
from src.engine.audio.sound_manager import SoundManager
from src.modules.sorcerer.module import SorcererModule

class TestAudioSubsystem(unittest.TestCase):
    """Test suite for HeroEngine audio subsystem, requests, backends, and SoundManager."""

    def test_audio_request_immutability_and_clamping(self):
        req_over = AudioRequest(sound_id="test", volume=1.5)
        self.assertEqual(req_over.volume, 1.0)

        req_under = AudioRequest(sound_id="test", volume=-0.5)
        self.assertEqual(req_under.volume, 0.0)

        with self.assertRaises(Exception):
            req_over.sound_id = "modified"  # Frozen dataclass immutability check

    def test_backend_factory_and_null_backend(self):
        null_backend = SoundBackendFactory.create_backend("null")
        self.assertIsInstance(null_backend, NullSoundBackend)
        self.assertTrue(null_backend.is_available())

        # Test safe repeated release
        null_backend.release()
        null_backend.release()

    def test_sound_manager_lazy_discovery_and_single_missing_logging(self):
        # Create temp dir with dummy sound file
        with tempfile.TemporaryDirectory() as temp_dir:
            dummy_sound_path = os.path.join(temp_dir, "shield_summon.wav")
            with open(dummy_sound_path, "w") as f:
                f.write("dummy wav content")

            manager = SoundManager(backend=NullSoundBackend())
            discovered = manager.discover_sounds(temp_dir)
            self.assertEqual(discovered, 1)
            self.assertTrue(manager.is_sound_registered("shield_summon"))
            self.assertNotIn("shield_summon", manager._loaded_assets)

            # First playback trigger causes lazy loading into backend
            reqs = [AudioRequest(sound_id="shield_summon", volume=0.8)]
            handles = manager.process_requests(reqs)
            self.assertEqual(len(handles), 1)
            self.assertIn("shield_summon", manager._loaded_assets)

            # Test single missing asset logging
            missing_req = [AudioRequest(sound_id="non_existent_spell")]
            manager.process_requests(missing_req)
            self.assertIn("non_existent_spell", manager._logged_missing_assets)
            
            # Second call shouldn't crash or re-add
            manager.process_requests(missing_req)
            self.assertEqual(len(manager._logged_missing_assets), 1)

            manager.release()

    def test_cooldown_debouncing_and_handles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dummy_sound_path = os.path.join(temp_dir, "whip_crack.wav")
            with open(dummy_sound_path, "w") as f:
                f.write("dummy wav content")

            manager = SoundManager(backend=NullSoundBackend())
            manager.discover_sounds(temp_dir)

            # Emit request with 200ms cooldown
            req = AudioRequest(sound_id="whip_crack", cooldown_ms=200.0)

            # First trigger -> processed
            h1 = manager.process_requests([req])
            self.assertEqual(len(h1), 1)

            # Immediate second trigger -> debounced!
            h2 = manager.process_requests([req])
            self.assertEqual(len(h2), 0)

            # Wait > 200ms
            time.sleep(0.22)

            # Third trigger -> processed!
            h3 = manager.process_requests([req])
            self.assertEqual(len(h3), 1)

            # Test stopping handles
            manager.stop_handle(h3[0])
            manager.stop_all()
            manager.release()

    def test_sorcerer_module_audio_request_harvesting(self):
        sorcerer = SorcererModule(config={})
        sorcerer.initialize()
        sorcerer.on_activate()

        # Simulate pinch gesture input
        from src.engine.core.input_manager import HandState
        dummy_landmarks = [(0.5, 0.5, 0.0)] * 21
        hand = HandState(label="Right", score=0.99, landmarks=dummy_landmarks, gesture="Pinch")
        sorcerer.process_input({"Right": hand})

        # Tick simulation
        sorcerer.update(0.016)

        # Harvest audio requests
        reqs = sorcerer.get_audio_requests()
        self.assertGreaterEqual(len(reqs), 1)
        self.assertEqual(reqs[0].sound_id, "spell_charge")

        # Second call to get_audio_requests should return empty list (stateless harvesting)
        empty_reqs = sorcerer.get_audio_requests()
        self.assertEqual(len(empty_reqs), 0)

        sorcerer.release()

if __name__ == "__main__":
    unittest.main()
