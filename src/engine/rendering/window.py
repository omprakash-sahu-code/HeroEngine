import glfw
import sys
from typing import Dict, Any, Callable
from src.engine.utils.logger import setup_logger

logger = setup_logger("Window")

class Window:
    """Manages GLFW window lifecycle, callbacks, and inputs."""

    def __init__(self, config: Dict[str, Any]):
        """Args:

            config: Dictionary containing display configuration.
        """
        self.config = config
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)
        self.title = config.get("title", "HeroEngine")
        self.fullscreen = config.get("fullscreen", False)
        self.vsync = config.get("vsync", True)
        
        self.handle = None
        self._resize_callbacks = []

        self._initialize_glfw()

    def _initialize_glfw(self) -> None:
        """Initialize GLFW library and create the window handle."""
        if not glfw.init():
            logger.critical("Failed to initialize GLFW")
            sys.exit(1)

        # Configure OpenGL hints (Require OpenGL 3.3 Core profile minimum)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

        monitor = glfw.get_primary_monitor() if self.fullscreen else None
        
        self.handle = glfw.create_window(
            self.width, self.height, self.title, monitor, None
        )
        
        if not self.handle:
            glfw.terminate()
            logger.critical("Failed to create GLFW window")
            sys.exit(1)

        glfw.make_context_current(self.handle)
        
        # Set swap interval (vsync)
        if self.vsync:
            glfw.swap_interval(1)
        else:
            glfw.swap_interval(0)

        # Register standard callbacks
        glfw.set_framebuffer_size_callback(self.handle, self._framebuffer_size_callback)

    def _framebuffer_size_callback(self, window, width: int, height: int) -> None:
        """Internal callback for when framebuffer size changes.

        Args:
            window: GLFW window pointer.
            width: New width.
            height: New height.
        """
        self.width = width
        self.height = height
        for cb in self._resize_callbacks:
            cb(width, height)

    def register_resize_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add a listener for window resize events."""
        self._resize_callbacks.append(callback)

    def should_close(self) -> bool:
        """Check if GLFW window should close.

        Returns:
            bool: True if close requested.
        """
        return bool(glfw.window_should_close(self.handle))

    def swap_buffers(self) -> None:
        """Swap front and back frame buffers."""
        glfw.swap_buffers(self.handle)

    def poll_events(self) -> None:
        """Poll incoming window/input events."""
        glfw.poll_events()

    def close(self) -> None:
        """Destroy window and terminate GLFW context."""
        if self.handle:
            glfw.destroy_window(self.handle)
            self.handle = None
        glfw.terminate()
        logger.info("GLFW Window destroyed successfully.")
