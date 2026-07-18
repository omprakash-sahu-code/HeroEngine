from typing import Dict, Any, Optional, List
from src.engine.utils.logger import setup_logger
from src.modules.base_module import HeroModule, ModuleState
from src.engine.core.module_registry import ModuleRegistry
from src.engine.core.module_loader import ModuleLoader

logger = setup_logger("ModuleManager")

class ModuleManager:
    """Controls runtime lifecycle, switching, activation, and safe hot-reloading of HeroModules."""

    def __init__(self, registry: ModuleRegistry, loader: ModuleLoader):
        self.registry = registry
        self.loader = loader
        self.loaded_instances: Dict[str, HeroModule] = {}
        self.active_module_id: Optional[str] = None

    @property
    def active_module(self) -> Optional[HeroModule]:
        """Returns the currently active HeroModule instance, or None if no module is active."""
        if self.active_module_id and self.active_module_id in self.loaded_instances:
            return self.loaded_instances[self.active_module_id]
        return None

    def initialize_module(self, module_id: str, config: Dict[str, Any]) -> Optional[HeroModule]:
        """Loads and initializes a module instance if not already initialized."""
        if module_id in self.loaded_instances:
            instance = self.loaded_instances[module_id]
            if not instance.is_initialized:
                try:
                    instance.initialize()
                    instance.state = ModuleState.INITIALIZED
                except Exception as e:
                    logger.error(f"Error initializing module '{module_id}': {e}", exc_info=True)
                    return None
            return instance

        # Instantiate new object
        instance = self.loader.instantiate(module_id, config)
        if not instance:
            return None

        try:
            instance.initialize()
            instance.state = ModuleState.INITIALIZED
            self.loaded_instances[module_id] = instance
            logger.info(f"Initialized module '{module_id}'")
            return instance
        except Exception as e:
            logger.error(f"Failed to initialize module '{module_id}': {e}", exc_info=True)
            return None

    def switch_module(self, target_id: str, config: Dict[str, Any]) -> Optional[HeroModule]:
        """Switches the active module from current to target_id safely.

        Args:
            target_id: ID of the module to activate.
            config: Configuration dictionary.

        Returns:
            Optional[HeroModule]: The newly activated HeroModule instance.
        """
        if not self.registry.is_registered(target_id):
            logger.error(f"Cannot switch to unregistered module '{target_id}'. Registered: {list(self.registry.list_all().keys())}")
            return self.active_module

        # 1. Deactivate current active module
        current = self.active_module
        if current and current.name != target_id:
            logger.info(f"Deactivating current module '{self.active_module_id}'...")
            try:
                current.on_deactivate()
            except Exception as e:
                logger.error(f"Error deactivating module '{self.active_module_id}': {e}")

        # 2. Ensure target module is instantiated and initialized
        target = self.initialize_module(target_id, config)
        if not target:
            logger.error(f"Could not switch to module '{target_id}' due to initialization failure.")
            return current

        # 3. Activate target module
        try:
            logger.info(f"Activating target module '{target_id}'...")
            target.on_activate()
            self.active_module_id = target_id
            return target
        except Exception as e:
            logger.error(f"Error activating target module '{target_id}': {e}", exc_info=True)
            return current

    def cycle_module(self, forward: bool = True, config: Dict[str, Any] = None) -> Optional[HeroModule]:
        """Cycles through registered modules in forward or backward order."""
        discovered = list(self.registry.list_all().keys())
        if not discovered:
            return None

        if len(discovered) == 1:
            return self.switch_module(discovered[0], config or {})

        current_id = self.active_module_id
        if current_id in discovered:
            idx = discovered.index(current_id)
            step = 1 if forward else -1
            next_idx = (idx + step) % len(discovered)
        else:
            next_idx = 0

        target_id = discovered[next_idx]
        logger.info(f"Cycling module ({'forward' if forward else 'backward'}): {current_id} -> {target_id}")
        return self.switch_module(target_id, config or {})

    def reload_active(self, config: Dict[str, Any]) -> Optional[HeroModule]:
        """Safely reloads the active module code and replaces the active instance.

        If reload fails (e.g. syntax error in code), the old working instance is retained.
        """
        if not self.active_module_id:
            logger.warning("No active module to reload.")
            return None

        target_id = self.active_module_id
        old_instance = self.active_module

        # Attempt reload via loader
        success, new_cls, err_msg = self.loader.reload_module(target_id)
        if not success or not new_cls:
            logger.warning(f"Reload rejected: {err_msg}. Keeping current instance running.")
            return old_instance

        # Safe replacement: Instantiate and initialize new object first
        try:
            new_instance = new_cls(config)
            new_instance.initialize()
            new_instance.state = ModuleState.INITIALIZED
            new_instance.on_activate()

            # Release old instance cleanly
            if old_instance:
                try:
                    old_instance.release()
                except Exception as e:
                    logger.warning(f"Warning during old instance release on reload: {e}")

            # Swap active instance reference
            self.loaded_instances[target_id] = new_instance
            logger.info(f"Successfully replaced active instance for module '{target_id}'")
            return new_instance

        except Exception as e:
            logger.error(f"Failed instantiating reloaded class for '{target_id}': {e}. Rollback to old instance.", exc_info=True)
            return old_instance

    def unload_module(self, module_id: str) -> None:
        """Safely releases and unloads a module instance."""
        if module_id in self.loaded_instances:
            instance = self.loaded_instances[module_id]
            try:
                instance.release()
            except Exception as e:
                logger.error(f"Error releasing module '{module_id}': {e}")
            del self.loaded_instances[module_id]
            if self.active_module_id == module_id:
                self.active_module_id = None
            logger.info(f"Unloaded module '{module_id}'")

    def unload_all(self) -> None:
        """Cleanly releases all loaded module instances."""
        for mod_id in list(self.loaded_instances.keys()):
            self.unload_module(mod_id)
