import os
from src.engine.utils.config import load_config
from src.engine.utils.logger import setup_logger
from src.engine.core.engine import ModuleManager

logger = setup_logger("Main")

def main():
    logger.info("Initializing HeroEngine Core...")
    
    # 1. Load Configurations
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "default.yaml")
    config_path = os.path.abspath(config_path)
    
    try:
        config = load_config(config_path)
        logger.info(f"Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return

    # 2. Discover and Load Hero Modules
    modules_dir = os.path.join(os.path.dirname(__file__), "modules")
    modules_dir = os.path.abspath(modules_dir)
    
    manager = ModuleManager(modules_dir)
    logger.info(f"Scanning for Hero Modules in: {modules_dir}")
    manager.discover_modules()
    
    # 3. Instantiate the configured active module
    active_module_name = config.get("module", {}).get("active", "sorcerer")
    logger.info(f"Activating module: '{active_module_name}'")
    
    active_module = manager.load_module(active_module_name, config)
    if active_module:
        logger.info(f"Successfully loaded {active_module.name.capitalize()} Module.")
        # Template hook initialization (requires OpenGL context in subsequent steps)
        # active_module.initialize(ctx)
    else:
        logger.error(f"Failed to load active module '{active_module_name}'")

if __name__ == "__main__":
    main()
