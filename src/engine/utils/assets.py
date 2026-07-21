import os
import glob
from typing import List, Tuple
from src.engine.utils.paths import resource_path

class AssetManifest:
    """Centralized manifest registering all engine subsystem asset dependencies."""

    @staticmethod
    def get_asset_rules() -> List[Tuple[str, str]]:
        """Return list of (relative_source_glob_or_dir, relative_target_dir) tuples."""
        return [
            ("config/default.yaml", "config"),
            ("src/engine/rendering/shaders", "src/engine/rendering/shaders"),
            ("src/modules", "src/modules"),
            ("src/assets/sounds", "src/assets/sounds"),
        ]

    @classmethod
    def get_engine_assets(cls) -> List[Tuple[str, str]]:
        """Resolve absolute source paths for PyInstaller datas collection.

        Returns:
            List[Tuple[str, str]]: List of (absolute_source_path, target_relative_directory)
        """
        datas: List[Tuple[str, str]] = []

        for rel_src, rel_target in cls.get_asset_rules():
            abs_src = resource_path(rel_src)
            if os.path.exists(abs_src):
                datas.append((abs_src, rel_target))

        return datas

    @classmethod
    def verify_all_assets(cls) -> List[str]:
        """Verify that all registered asset dependencies exist and are readable.

        Returns:
            List[str]: List of missing asset paths (empty list if all valid).
        """
        missing: List[str] = []

        for rel_src, _ in cls.get_asset_rules():
            abs_src = resource_path(rel_src)
            if not os.path.exists(abs_src):
                missing.append(rel_src)

        return missing
