import moderngl
from typing import Tuple
from src.engine.utils.logger import setup_logger

logger = setup_logger("Framebuffer")

class Framebuffer:
    """Manages custom ModernGL Framebuffers for post-processing passes."""

    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        """Args:

            ctx: ModernGL context.
            width: Target width.
            height: Target height.
        """
        self.ctx = ctx
        self.width = width
        self.height = height
        
        self.fbo = None
        self.color_texture = None
        self.depth_renderbuffer = None

        self._create_fbo()

    def _create_fbo(self) -> None:
        """Initialize offscreen render targets."""
        try:
            # Color Attachment
            self.color_texture = self.ctx.texture(
                (self.width, self.height), 4
            )  # RGBA target
            self.color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            # Depth Attachment
            self.depth_renderbuffer = self.ctx.depth_renderbuffer(
                (self.width, self.height)
            )

            # Build Framebuffer
            self.fbo = self.ctx.framebuffer(
                color_attachments=[self.color_texture],
                depth_attachment=self.depth_renderbuffer
            )
        except Exception as e:
            logger.error(f"Failed to create Framebuffer Object: {e}")
            raise e

    def bind(self) -> None:
        """Bind this framebuffer as the active render target."""
        if self.fbo:
            self.fbo.use()

    def unbind(self) -> None:
        """Restore screen framebuffer as active render target."""
        self.ctx.screen.use()

    def clear(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0) -> None:
        """Clear color and depth components of the off-screen buffer."""
        if self.fbo:
            self.fbo.clear(r, g, b, a)

    def release(self) -> None:
        """Clean up buffers and associated textures."""
        if self.color_texture:
            self.color_texture.release()
            self.color_texture = None
        if self.depth_renderbuffer:
            self.depth_renderbuffer.release()
            self.depth_renderbuffer = None
        if self.fbo:
            self.fbo.release()
            self.fbo = None
