import unittest
import os
import tempfile
import json
from src.engine.core.module_registry import ModuleRegistry
from src.engine.core.module_loader import ModuleLoader
from src.engine.core.module_manager import ModuleManager
from src.modules.base_module import HeroModule, ModuleState

class MockLifecycleModule(HeroModule):
    @property
    def name(self) -> str:
        return "lifecycle_mock"

    def initialize(self):
        self.state = ModuleState.INITIALIZED
        self.lifecycle_log = ["initialize"]

    def on_activate(self):
        super().on_activate()
        self.lifecycle_log.append("on_activate")

    def process_input(self, hands):
        self.lifecycle_log.append("process_input")

    def update(self, dt):
        self.lifecycle_log.append("update")

    def get_render_requests(self):
        return []

    def on_deactivate(self):
        super().on_deactivate()
        self.lifecycle_log.append("on_deactivate")

    def release(self):
        super().release()
        self.lifecycle_log.append("release")


class TestPluginArchitecture(unittest.TestCase):
    """Test suite covering ModuleRegistry, ModuleLoader, ModuleManager, and rollback safety."""

    def test_registry_manifest_fallback_and_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Valid module with custom manifest.json
            valid_dir = os.path.join(temp_dir, "hero_alpha")
            os.makedirs(valid_dir)
            with open(os.path.join(valid_dir, "module.py"), "w") as f:
                f.write("# empty")
            with open(os.path.join(valid_dir, "manifest.json"), "w") as f:
                json.dump({"name": "Hero Alpha", "version": "3.0.0"}, f)

            # 2. Module with missing manifest (should generate defaults)
            no_manifest_dir = os.path.join(temp_dir, "hero_beta")
            os.makedirs(no_manifest_dir)
            with open(os.path.join(no_manifest_dir, "module.py"), "w") as f:
                f.write("# empty")

            # 3. Module with malformed manifest (invalid JSON)
            malformed_dir = os.path.join(temp_dir, "hero_gamma")
            os.makedirs(malformed_dir)
            with open(os.path.join(malformed_dir, "module.py"), "w") as f:
                f.write("# empty")
            with open(os.path.join(malformed_dir, "manifest.json"), "w") as f:
                f.write("{ invalid json format }")

            # 4. Folder without module.py (should be ignored)
            ignored_dir = os.path.join(temp_dir, "not_a_module")
            os.makedirs(ignored_dir)

            registry = ModuleRegistry(temp_dir)
            registry.discover()

            # Assertions
            self.assertTrue(registry.is_registered("hero_alpha"))
            self.assertEqual(registry.get_manifest("hero_alpha")["name"], "Hero Alpha")
            self.assertEqual(registry.get_manifest("hero_alpha")["version"], "3.0.0")

            self.assertTrue(registry.is_registered("hero_beta"))
            self.assertEqual(registry.get_manifest("hero_beta")["name"], "Hero_beta")

            self.assertTrue(registry.is_registered("hero_gamma"))
            self.assertEqual(registry.get_manifest("hero_gamma")["name"], "Hero_gamma")

            self.assertFalse(registry.is_registered("not_a_module"))

    def test_full_lifecycle_sequence(self):
        mod = MockLifecycleModule({})
        self.assertEqual(mod.state, ModuleState.LOADED)

        mod.initialize()
        self.assertEqual(mod.state, ModuleState.INITIALIZED)

        mod.on_activate()
        self.assertEqual(mod.state, ModuleState.ACTIVE)

        mod.process_input({})
        mod.update(0.016)

        mod.on_deactivate()
        self.assertEqual(mod.state, ModuleState.INITIALIZED)

        mod.release()
        self.assertEqual(mod.state, ModuleState.UNLOADED)

        expected_log = ["initialize", "on_activate", "process_input", "update", "on_deactivate", "release"]
        self.assertEqual(mod.lifecycle_log, expected_log)

    def test_stateless_audio_request_harvesting(self):
        mod = MockLifecycleModule({})
        mod.emit_sound("spell_cast", volume=0.8)
        mod.emit_sound("whip_crack", volume=1.0)

        # First harvest retrieves the two requests
        reqs1 = mod.get_audio_requests()
        self.assertEqual(len(reqs1), 2)
        self.assertEqual(reqs1[0].sound_id, "spell_cast")
        self.assertEqual(reqs1[1].sound_id, "whip_crack")

        # Second harvest on next frame must return empty list (stateless flush)
        reqs2 = mod.get_audio_requests()
        self.assertEqual(len(reqs2), 0)

    def test_hot_reload_rollback_on_syntax_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mod_dir = os.path.join(temp_dir, "reload_test")
            os.makedirs(mod_dir)
            code_path = os.path.join(mod_dir, "module.py")

            valid_code = """
from src.modules.base_module import HeroModule

class ReloadModule(HeroModule):
    def name(self):
        return "reload_test"
    def initialize(self):
        self.val = 100
    def process_input(self, hands):
        pass
    def update(self, dt):
        pass
    def get_render_requests(self):
        return []
    def release(self):
        super().release()
"""
            with open(code_path, "w") as f:
                f.write(valid_code)

            registry = ModuleRegistry(temp_dir)
            registry.discover()
            loader = ModuleLoader(registry)
            manager = ModuleManager(registry, loader)

            active = manager.switch_module("reload_test", {})
            self.assertIsNotNone(active)
            self.assertEqual(active.val, 100)

            # Inject SYNTAX ERROR into module file
            broken_code = """
from src.modules.base_module import HeroModule

class ReloadModule(HeroModule):
    def name(self):
        # INTENTIONAL SYNTAX ERROR BELOW
        def invalid_syntax(
"""
            with open(code_path, "w") as f:
                f.write(broken_code)

            # Attempt reload
            reloaded = manager.reload_active({})

            # Verify that reload safely rejected broken code and kept old instance active!
            self.assertEqual(reloaded, active)
            self.assertEqual(manager.active_module.val, 100)
            self.assertEqual(manager.active_module.state, ModuleState.ACTIVE)

if __name__ == "__main__":
    unittest.main()
