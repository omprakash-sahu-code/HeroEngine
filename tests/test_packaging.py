import os
import sys
import unittest
from unittest.mock import patch

from src.engine.utils.paths import resource_path
from src.engine.utils.assets import AssetManifest

class TestPackaging(unittest.TestCase):
    """Test suite covering resource_path resolution, sys._MEIPASS isolation, and AssetManifest completeness."""

    def test_canonical_resource_path_resolution(self):
        config_p = resource_path("config/default.yaml")
        self.assertTrue(os.path.isabs(config_p))
        self.assertTrue(config_p.endswith(os.path.join("config", "default.yaml")))

    def test_relative_path_normalization(self):
        p1 = resource_path("config/default.yaml")
        p2 = resource_path("./config/default.yaml")
        p3 = resource_path("config\\default.yaml")

        self.assertEqual(p1, p2)
        self.assertEqual(p1, p3)

    def test_simulated_frozen_mode_meipass_isolation(self):
        mock_meipass = os.path.abspath("temp_mock_dist")
        
        with patch.object(sys, 'frozen', True, create=True), \
             patch.object(sys, '_MEIPASS', mock_meipass, create=True):
            
            res_p = resource_path("config/default.yaml")
            expected_p = os.path.abspath(os.path.join(mock_meipass, "config", "default.yaml"))
            self.assertEqual(res_p, expected_p)

    def test_asset_manifest_completeness(self):
        missing = AssetManifest.verify_all_assets()
        self.assertEqual(missing, [], f"Missing required engine assets: {missing}")

        datas = AssetManifest.get_engine_assets()
        self.assertTrue(len(datas) >= 4)
        for abs_src, target_rel in datas:
            self.assertTrue(os.path.isabs(abs_src))
            self.assertTrue(os.path.exists(abs_src))

    def test_cross_platform_path_separators(self):
        res_unix = resource_path("src/engine/rendering/shaders/hud.frag")
        res_win = resource_path("src\\engine\\rendering\\shaders\\hud.frag")
        self.assertEqual(res_unix, res_win)

if __name__ == "__main__":
    unittest.main()
