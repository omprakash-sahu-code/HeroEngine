import sys
import os
import importlib
import importlib.util
import inspect
from typing import Dict, Type, Any, Optional, Tuple
from src.engine.utils.logger import setup_logger
from src.modules.base_module import HeroModule
from src.engine.core.module_registry import ModuleRegistry

logger = setup_logger("ModuleLoader")

class ModuleLoader:
    """Handles dynamic loading, instantiation, and safe hot-reloading of HeroModule classes."""

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
        self.classes: Dict[str, Type[HeroModule]] = {}
        self.imported_libs: Dict[str, Any] = {}

    def load_class(self, module_id: str) -> Optional[Type[HeroModule]]:
        """Imports and extracts the HeroModule subclass for a registered module ID."""
        if module_id in self.classes:
            return self.classes[module_id]

        manifest = self.registry.get_manifest(module_id)
        if not manifest or "entry_point" not in manifest:
            logger.error(f"Cannot load module '{module_id}': Not found in registry.")
            return None

        entry_point = manifest["entry_point"]
        module_name = f"hero_plugin_{module_id}"

        # Add modules parent directory to sys.path if not present
        modules_parent = os.path.dirname(self.registry.modules_dir)
        if modules_parent not in sys.path:
            sys.path.insert(0, modules_parent)

        try:
            spec = importlib.util.spec_from_file_location(module_name, entry_point)
            if not spec or not spec.loader:
                logger.error(f"Failed to create module spec for '{entry_point}'")
                return None

            lib = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = lib
            spec.loader.exec_module(lib)
            self.imported_libs[module_id] = (spec, lib)

            # Scan for subclass of HeroModule
            for name, obj in inspect.getmembers(lib):
                if (inspect.isclass(obj) and 
                        issubclass(obj, HeroModule) and 
                        obj is not HeroModule):
                    self.classes[module_id] = obj
                    logger.info(f"Loaded class '{name}' for module '{module_id}'")
                    return obj

            logger.error(f"No HeroModule subclass found in '{entry_point}'")
            return None
        except Exception as e:
            logger.error(f"Failed loading python module '{entry_point}': {e}", exc_info=True)
            return None

    def instantiate(self, module_id: str, config: Dict[str, Any]) -> Optional[HeroModule]:
        """Creates a new instance of a HeroModule."""
        cls = self.load_class(module_id)
        if not cls:
            return None

        try:
            instance = cls(config)
            logger.info(f"Instantiated new instance of '{module_id}'")
            return instance
        except Exception as e:
            logger.error(f"Error instantiating module '{module_id}': {e}", exc_info=True)
            return None

    def reload_module(self, module_id: str) -> Tuple[bool, Optional[Type[HeroModule]], str]:
        """Performs a safe hot-reload of the module code.

        Returns:
            Tuple[bool, Optional[Type[HeroModule]], str]: (success, new_class, error_message)
            If reload fails, returns False and the previous class is preserved without crashing.
        """
        if module_id not in self.imported_libs:
            cls = self.load_class(module_id)
            if cls:
                return True, cls, ""
            return False, None, "Module was not loaded and initial load failed."

        spec, old_lib = self.imported_libs[module_id]
        old_class = self.classes.get(module_id)
        manifest = self.registry.get_manifest(module_id)

        if not manifest or "entry_point" not in manifest:
            return False, old_class, "Manifest missing during reload."

        entry_point = manifest["entry_point"]
        module_name = f"hero_plugin_{module_id}"

        try:
            logger.info(f"Attempting safe hot reload of module '{module_id}'...")
            new_spec = importlib.util.spec_from_file_location(module_name, entry_point)
            if not new_spec or not new_spec.loader:
                raise ImportError(f"Could not build spec for reload of '{entry_point}'")

            new_lib = importlib.util.module_from_spec(new_spec)
            # Execute in sandbox lib first before binding to sys.modules
            new_spec.loader.exec_module(new_lib)

            # Locate updated subclass
            new_class = None
            for name, obj in inspect.getmembers(new_lib):
                if (inspect.isclass(obj) and 
                        issubclass(obj, HeroModule) and 
                        obj is not HeroModule):
                    new_class = obj
                    break

            if not new_class:
                raise ImportError(f"No HeroModule subclass found after reload of '{module_id}'.")

            # Update sys.modules and cache only on success
            sys.modules[module_name] = new_lib
            self.imported_libs[module_id] = (new_spec, new_lib)
            self.classes[module_id] = new_class
            logger.info(f"Successfully hot-reloaded module '{module_id}'")
            return True, new_class, ""

        except Exception as e:
            err_msg = f"Hot reload failed for '{module_id}': {e}"
            logger.warning(f"{err_msg} - Rolling back to previous version.")
            if old_class:
                self.classes[module_id] = old_class
            return False, old_class, err_msg
