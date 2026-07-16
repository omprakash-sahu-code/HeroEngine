import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
from src.engine.rendering.particles.gpu_particles import GPUParticleSystem, ParticleSimulationMode

class TestParticlePresets(unittest.TestCase):
    """Tests the loading, parsing, and hot-reloading of data-driven particle presets."""

    def setUp(self):
        # Create a mock ModernGL context to avoid driver initialization during tests
        self.mock_ctx = MagicMock()
        
        # Patch _initialize_resources so we don't compile actual GLSL shaders
        self.init_resources_patcher = patch.object(GPUParticleSystem, '_initialize_resources')
        self.mock_init_resources = self.init_resources_patcher.start()

    def tearDown(self):
        self.init_resources_patcher.stop()

    def test_presets_parsing(self):
        # Sample configuration dictionary
        config = {
            "particle_presets": {
                "test_ballistic": {
                    "color": [1.0, 0.0, 0.0],
                    "speed": 0.5,
                    "mode": "ballistic",
                    "lifetime_min": 0.2,
                    "lifetime_max": 0.5
                },
                "test_spiral": {
                    "color": [0.0, 1.0, 0.0],
                    "speed": 0.0,
                    "mode": "spiral",
                    "lifetime_min": 1.0,
                    "lifetime_max": 1.5
                }
            }
        }
        
        # Instantiate system with custom config
        gpu_particles = GPUParticleSystem(self.mock_ctx, limit=1000, config=config)
        
        # Verify presets parsed correctly
        self.assertIn("test_ballistic", gpu_particles.presets)
        self.assertIn("test_spiral", gpu_particles.presets)
        
        ballistic = gpu_particles.presets["test_ballistic"]
        self.assertEqual(ballistic["color"], (1.0, 0.0, 0.0))
        self.assertEqual(ballistic["speed"], 0.5)
        self.assertEqual(ballistic["mode"], ParticleSimulationMode.BALLISTIC)
        self.assertEqual(ballistic["lifetime_min"], 0.2)
        self.assertEqual(ballistic["lifetime_max"], 0.5)
        
        spiral = gpu_particles.presets["test_spiral"]
        self.assertEqual(spiral["color"], (0.0, 1.0, 0.0))
        self.assertEqual(spiral["speed"], 0.0)
        self.assertEqual(spiral["mode"], ParticleSimulationMode.SPIRAL)
        self.assertEqual(spiral["lifetime_min"], 1.0)
        self.assertEqual(spiral["lifetime_max"], 1.5)

    def test_presets_fallback_and_reload(self):
        # Create a temp default.yaml to test fallback disk loading and hot-reloading
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "default.yaml")
            
            initial_content = """
particle_presets:
  temp_preset:
    color: [0.5, 0.5, 0.5]
    speed: 0.1
    mode: "ballistic"
"""
            with open(config_file, "w") as f:
                f.write(initial_content)
                
            # Instantiate particle system and override config path
            gpu_particles = GPUParticleSystem(self.mock_ctx, limit=1000)
            gpu_particles.config_path = config_file
            
            # Force trigger reload
            gpu_particles._check_and_reload_presets()
            
            self.assertIn("temp_preset", gpu_particles.presets)
            self.assertEqual(gpu_particles.presets["temp_preset"]["color"], (0.5, 0.5, 0.5))
            
            # Modify and save configuration
            updated_content = """
particle_presets:
  temp_preset:
    color: [0.0, 0.0, 1.0]
    speed: 0.9
    mode: "spiral"
    lifetime_min: 0.8
    lifetime_max: 1.2
"""
            with open(config_file, "w") as f:
                f.write(updated_content)
            
            # Backdate last_config_mtime to trigger reload logic
            gpu_particles.last_config_mtime = 0.0
            gpu_particles._check_and_reload_presets()
            
            # Verify hot reload modified the internal dict correctly
            self.assertEqual(gpu_particles.presets["temp_preset"]["color"], (0.0, 0.0, 1.0))
            self.assertEqual(gpu_particles.presets["temp_preset"]["mode"], ParticleSimulationMode.SPIRAL)
            self.assertEqual(gpu_particles.presets["temp_preset"]["lifetime_min"], 0.8)
            self.assertEqual(gpu_particles.presets["temp_preset"]["lifetime_max"], 1.2)

if __name__ == "__main__":
    unittest.main()
