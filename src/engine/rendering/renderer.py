import moderngl
from typing import Tuple
from src.engine.utils.logger import setup_logger

logger = setup_logger("Renderer")

class Renderer:
    """Manages the ModernGL rendering context, states, and global draw bindings."""

    def __init__(self):
        self.ctx = None
        self._initialize_context()

    def _initialize_context(self) -> None:
        """Detect or create the active OpenGL/ModernGL context."""
        try:
            # Assumes a window context is already active (via GLFW)
            self.ctx = moderngl.create_context()
            logger.info(f"ModernGL context created. OpenGL Version: {self.ctx.info['GL_VERSION']}")
            
            # Configure default state flags
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (
                moderngl.SRC_ALPHA,
                moderngl.ONE_MINUS_SRC_ALPHA
            )
        except Exception as e:
            logger.critical(f"Failed to initialize ModernGL context: {e}")
            raise e

    def clear(self, color: Tuple[float, float, float, float] = (0.1, 0.1, 0.1, 1.0)) -> None:
        """Clear the current framebuffer to target color.

        Args:
            color: Tuple containing (r, g, b, a) clear colors.
        """
        if self.ctx:
            self.ctx.clear(*color)

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Update active rendering viewport size."""
        if self.ctx:
            self.ctx.viewport = (x, y, width, height)

    def set_blend_mode_additive(self) -> None:
        """Configure additive blending (ideal for glowing effects)."""
        if self.ctx:
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)

    def set_blend_mode_alpha(self) -> None:
        """Configure standard alpha transparency blending."""
        if self.ctx:
            self.ctx.blend_func = (
                moderngl.SRC_ALPHA,
                moderngl.ONE_MINUS_SRC_ALPHA
            )
