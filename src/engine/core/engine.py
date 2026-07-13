import os
import sys
import importlib
import inspect
from typing import Dict, Type, Any, Optional

from src.engine.utils.logger import setup_logger
from src.modules.base_module import HeroModule

logger = setup_logger("EngineCore")

class ModuleManager:
    """Manages discovery, dynamic loading, and lifecycle of HeroModule plugins."""

    def __init__(self, modules_dir: str):
        """Args:

            modules_dir: Directory containing hero modules.
        """
        self.modules_dir = os.path.abspath(modules_dir)
        self.loaded_modules: Dict[str, HeroModule] = {}
        self.available_classes: Dict[str, Type[HeroModule]] = {}
        
        # Add modules parent directory to sys.path if not present
        parent_dir = os.path.dirname(self.modules_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

    def discover_modules(self) -> None:
        """Scan the modules directory for folders containing module.py files

        and loads subclasses of HeroModule.
        """
        if not os.path.isdir(self.modules_dir):
            logger.error(f"Modules directory does not exist: {self.modules_dir}")
            return

        for item in os.listdir(self.modules_dir):
            module_path = os.path.join(self.modules_dir, item)
            if not os.path.isdir(module_path):
                continue
                
            # Check for module.py entry point
            module_file = os.path.join(module_path, "module.py")
            if not os.path.isfile(module_file):
                continue

            try:
                # Dynamic import
                # Relative import format: src.modules.{folder_name}.module
                import_name = f"src.modules.{item}.module"
                imported_lib = importlib.import_module(import_name)
                
                # Scan for subclasses of HeroModule inside imported module
                for name, obj in inspect.getmembers(imported_lib):
                    if (inspect.isclass(obj) and 
                            issubclass(obj, HeroModule) and 
                            obj is not HeroModule):
                        
                        # Register the class type under its folder name
                        self.available_classes[item] = obj
                        logger.info(f"Discovered Hero Module: '{item}' -> class '{name}'")
            except Exception as e:
                logger.error(f"Failed to load module '{item}': {e}", exc_info=True)

    def load_module(self, module_name: str, config: Dict[str, Any]) -> Optional[HeroModule]:
        """Instantiates a discovered module.

        Args:
            module_name: Key name of the module (e.g. 'sorcerer').
            config: Configuration dictionary parameter to pass to initialization.

        Returns:
            Optional[HeroModule]: The loaded module instance, or None if load fails.
        """
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]

        if module_name not in self.available_classes:
            logger.error(f"Requested module '{module_name}' is not discovered or registered.")
            return None

        try:
            module_class = self.available_classes[module_name]
            instance = module_class(config)
            self.loaded_modules[module_name] = instance
            logger.info(f"Successfully instantiated module '{module_name}'")
            return instance
        except Exception as e:
            logger.error(f"Failed to instantiate module '{module_name}': {e}", exc_info=True)
            return None
