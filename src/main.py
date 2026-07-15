import os
import sys
from src.engine.utils.config import load_config
from src.engine.utils.logger import setup_logger
from src.engine.rendering.window import Window
from src.engine.rendering.renderer import Renderer

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
        sys.exit(1)

    # 2. Initialize GLFW Window
    display_config = config.get("display", {})
    window = Window(display_config)
    logger.info(f"Window initialized: {window.width}x{window.height}")

    # 3. Initialize ModernGL Renderer Context
    try:
        renderer = Renderer()
    except Exception as e:
        logger.critical(f"Failed to boot renderer: {e}")
        window.close()
        sys.exit(1)

    # 4. Bind window resize to update renderer viewport
    window.register_resize_callback(lambda w, h: renderer.set_viewport(0, 0, w, h))
    renderer.set_viewport(0, 0, window.width, window.height)

    # Test Background Clear Color (Solid slate grey for Bootstrap verification)
    clear_color = (0.15, 0.17, 0.20, 1.0)
    logger.info("Entering primary engine bootstrap frame loop. Press ESC or close window to exit.")

    # 5. Main Bootstrap Loop
    while not window.should_close():
        # Clear frame buffer
        renderer.clear(clear_color)
        
        # Swap screen front and back buffers
        window.swap_buffers()
        
        # Poll events
        window.poll_events()

    # 6. Cleanup resources
    window.close()
    logger.info("HeroEngine shutdown cleanly.")

if __name__ == "__main__":
    main()
