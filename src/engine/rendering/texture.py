import moderngl
from typing import Tuple
from src.engine.utils.logger import setup_logger

logger = setup_logger("Texture")

class Texture2D:
    """Wraps ModernGL texture creation and pixel buffer updates."""

    def __init__(self, ctx: moderngl.Context, width: int, height: int, components: int = 3):
        """Args:

            ctx: ModernGL context.
            width: Width of texture.
            height: Height of texture.
            components: Number of channels (e.g. 3 for RGB, 4 for RGBA).
        """
        self.ctx = ctx
        self.width = width
        self.height = height
        self.components = components
        self.texture = None

        self._create_texture()

    def _create_texture(self) -> None:
        """Create empty texture resource."""
        try:
            self.texture = self.ctx.texture(
                (self.width, self.height),
                self.components,
                data=None
            )
            # Default filtering: linear interpolations
            self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.texture.repeat_x = False
            self.texture.repeat_y = False
        except Exception as e:
            logger.error(f"Failed to create 2D texture: {e}")
            raise e

    def write(self, data: bytes) -> None:
        """Upload raw pixel bytes directly to the GPU texture memory.

        Args:
            data: Raw pixel bytes (must match texture dimensions * components).
        """
        if self.texture and data:
            try:
                self.texture.write(data)
            except Exception as e:
                logger.error(f"Failed to upload data to texture: {e}")

    def use(self, location: int = 0) -> None:
        """Bind the texture to a specific hardware texture sampler slot.

        Args:
            location: The texture unit index (default 0).
        """
        if self.texture:
            self.texture.use(location)

    def release(self) -> None:
        """Deallocate texture resource."""
        if self.texture:
            self.texture.release()
            self.texture = None
