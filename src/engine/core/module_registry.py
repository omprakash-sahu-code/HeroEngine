import os
import json
from typing import Dict, List, Any, Optional
from src.engine.utils.logger import setup_logger
from src.engine.utils.paths import resource_path

logger = setup_logger("ModuleRegistry")

class ModuleRegistry:
    """Discovers, parses, and caches metadata manifests for all hero modules."""

    def __init__(self, modules_dir: str):
        """Args:
            modules_dir: Directory containing hero module folders.
        """
        resolved = resource_path(modules_dir) if not os.path.isabs(modules_dir) else modules_dir
        if not os.path.exists(resolved):
            resolved = resource_path(modules_dir)
        self.modules_dir = os.path.abspath(resolved)
        self._registry: Dict[str, Dict[str, Any]] = {}

    def discover(self) -> None:
        """Scans the modules directory for valid folders containing module.py

        and populates the internal metadata cache.
        """
        self._registry.clear()

        if not os.path.isdir(self.modules_dir):
            logger.error(f"Modules directory does not exist: {self.modules_dir}")
            return

        for item in os.listdir(self.modules_dir):
            module_path = os.path.join(self.modules_dir, item)
            if not os.path.isdir(module_path):
                continue

            # Check for required entry point: module.py
            module_file = os.path.join(module_path, "module.py")
            if not os.path.isfile(module_file):
                continue

            # Standard manifest schema defaults
            manifest = {
                "id": item,
                "name": item.capitalize(),
                "version": "1.0.0",
                "author": "HeroEngine",
                "description": "HeroEngine Plugin Module",
                "icon": "icon.png",
                "entry": "module.py",
                "engine": ">=1.0.0",
                "module_dir": module_path,
                "entry_point": module_file
            }

            # Attempt to parse custom manifest.json if present
            manifest_file = os.path.join(module_path, "manifest.json")
            if os.path.isfile(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        user_manifest = json.load(f)
                        if isinstance(user_manifest, dict):
                            manifest.update(user_manifest)
                        else:
                            logger.warning(f"Manifest for '{item}' is not a JSON object. Using defaults.")
                except Exception as e:
                    logger.warning(f"Failed parsing manifest.json for '{item}': {e}. Using defaults.")

            # Ensure entry_point and module_dir stay correctly anchored
            manifest["module_dir"] = module_path
            manifest["entry_point"] = module_file

            self._registry[item] = manifest
            logger.info(f"Registered Hero Module '{item}' ({manifest['name']} v{manifest['version']})")

    def get_manifest(self, module_id: str) -> Optional[Dict[str, Any]]:
        """Returns cached manifest metadata for a given module ID."""
        return self._registry.get(module_id)

    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """Returns a copy of all registered module manifests dict."""
        return dict(self._registry)

    def list_modules(self) -> List[Dict[str, Any]]:
        """Returns a list of all registered module manifest dictionaries."""
        return list(self._registry.values())

    def is_registered(self, module_id: str) -> bool:
        """Returns True if module_id exists in registry."""
        return module_id in self._registry
