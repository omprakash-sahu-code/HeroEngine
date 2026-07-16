import os
import numpy as np
import moderngl
from typing import Dict, Any
from src.engine.rendering.framebuffer import Framebuffer
from src.engine.rendering.shader import ShaderProgram
from src.engine.utils.logger import setup_logger

logger = setup_logger("PostProcessingPipeline")

class PostProcessingPipeline:
    """Manages the full-screen offscreen rendering passes, including

    luminance thresholding, downscaled separable Gaussian blur,
    and HDR tone mapped final compositing.
    """

    def __init__(self, ctx: moderngl.Context, width: int, height: int, config: Dict[str, Any]):
        self.ctx = ctx
        self.width = width
        self.height = height
        
        # Load configs
        pp_config = config.get("post_processing", {})
        self.enabled = pp_config.get("enabled", True)
        self.threshold = pp_config.get("threshold", 0.6)
        self.bloom_intensity = pp_config.get("bloom_intensity", 1.2)
        self.exposure = pp_config.get("exposure", 1.0)
        self.gamma = pp_config.get("gamma", 2.2)
        self.downsample_factor = pp_config.get("downsample_factor", 2)
        
        # Framebuffer containers
        self.scene_fbo = None
        self.bright_fbo = None
        self.blur_fbo_h = None
        self.blur_fbo_v = None
        
        # Shaders
        self.threshold_shader = None
        self.blur_shader = None
        self.blend_shader = None
        
        # Screen quad geometry
        self.quad_vao = None
        self.quad_vbo = None
        
        self._initialize_resources()

    def _initialize_resources(self) -> None:
        """Allocate framebuffers, compile shaders, and setup quad geometry."""
        # 1. Create Framebuffers
        self._create_fbos()
        
        # 2. Compile shaders
        shader_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shaders")
        vert_path = os.path.join(shader_dir, "post_common.vert")
        
        try:
            self.threshold_shader = ShaderProgram(
                self.ctx, vert_path, os.path.join(shader_dir, "threshold.frag")
            )
            self.blur_shader = ShaderProgram(
                self.ctx, vert_path, os.path.join(shader_dir, "blur.frag")
            )
            self.blend_shader = ShaderProgram(
                self.ctx, vert_path, os.path.join(shader_dir, "bloom_blend.frag")
            )
            logger.info("Successfully compiled all post-processing shader programs.")
        except Exception as e:
            logger.critical(f"Failed to compile post-processing shaders: {e}")
            raise e
            
        # 3. Setup unit quad vertices (X, Y in [-1, 1], U, V in [0, 1])
        quad_vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
            
            -1.0,  1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype='f4')
        
        self.quad_vbo = self.ctx.buffer(quad_vertices.tobytes())
        # Use any program to declare vertex format
        self.quad_vao = self.ctx.vertex_array(
            self.threshold_shader.program,
            [(self.quad_vbo, '2f 2f', 'in_position', 'in_texcoord')]
        )

    def _create_fbos(self) -> None:
        """Create full-res scene buffer and downscaled bloom buffers."""
        # Clean up existing first if resizing
        self._release_fbos()
        
        # Scene FBO is full resolution with depth (needed for background quad + overlays)
        self.scene_fbo = Framebuffer(self.ctx, self.width, self.height, with_depth=True)
        
        # Downsampled dimensions for bloom blur (improves performance and blur size)
        self.down_width = max(1, self.width // self.downsample_factor)
        self.down_height = max(1, self.height // self.downsample_factor)
        
        # Downsampled auxiliary buffers (no depth buffer needed)
        self.bright_fbo = Framebuffer(self.ctx, self.down_width, self.down_height, with_depth=False)
        self.blur_fbo_h = Framebuffer(self.ctx, self.down_width, self.down_height, with_depth=False)
        self.blur_fbo_v = Framebuffer(self.ctx, self.down_width, self.down_height, with_depth=False)
        
        logger.info(
            f"Allocated post-processing FBOs. Scene: {self.width}x{self.height} | "
            f"Bloom Buffers: {self.down_width}x{self.down_height} (factor={self.downsample_factor})"
        )

    def resize(self, width: int, height: int) -> None:
        """Recreate framebuffers to match viewport modifications."""
        if width == self.width and height == self.height:
            return
            
        self.width = width
        self.height = height
        self._create_fbos()

    def begin(self) -> None:
        """Bind offscreen scene buffer as active render target."""
        if self.enabled and self.scene_fbo:
            self.scene_fbo.bind()
            self.scene_fbo.clear(0.0, 0.0, 0.0, 1.0)

    def end(self) -> None:
        """Restore screen buffer and process post-processing shader passes."""
        if not self.enabled or not self.scene_fbo:
            self.ctx.screen.use()
            return
            
        # Clear color states to draw screen quads
        self.ctx.disable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)
        
        # 1. High-Pass Filter Pass (Isolate highlights)
        self.bright_fbo.bind()
        self.bright_fbo.clear(0.0, 0.0, 0.0, 1.0)
        self.threshold_shader.use()
        self.threshold_shader.set_uniform("u_threshold", self.threshold)
        self.scene_fbo.color_texture.use(0)
        self.threshold_shader.set_uniform("u_texture", 0)
        self.quad_vao.render(moderngl.TRIANGLES)
        
        # 2. Separable Blur Pass (Ping-pong vertical and horizontal)
        # First iteration: blur bright_fbo into blur_fbo_h, then blur_fbo_h into blur_fbo_v
        self.blur_shader.use()
        
        # Pass 1: Horizontal Blur
        self.blur_fbo_h.bind()
        self.blur_fbo_h.clear(0.0, 0.0, 0.0, 1.0)
        self.blur_shader.set_uniform("u_horizontal", True)
        self.blur_shader.set_uniform("u_texel_size", 1.0 / self.down_width)
        self.bright_fbo.color_texture.use(0)
        self.blur_shader.set_uniform("u_texture", 0)
        self.quad_vao.render(moderngl.TRIANGLES)
        
        # Pass 2: Vertical Blur
        self.blur_fbo_v.bind()
        self.blur_fbo_v.clear(0.0, 0.0, 0.0, 1.0)
        self.blur_shader.set_uniform("u_horizontal", False)
        self.blur_shader.set_uniform("u_texel_size", 1.0 / self.down_height)
        self.blur_fbo_h.color_texture.use(0)
        self.blur_shader.set_uniform("u_texture", 0)
        self.quad_vao.render(moderngl.TRIANGLES)
        
        # 3. Final Composite & HDR Blending (Draw to standard screen)
        self.ctx.screen.use()
        self.ctx.screen.clear(0.0, 0.0, 0.0, 1.0)
        
        self.blend_shader.use()
        self.blend_shader.set_uniform("u_bloom_intensity", self.bloom_intensity)
        self.blend_shader.set_uniform("u_exposure", self.exposure)
        self.blend_shader.set_uniform("u_gamma", self.gamma)
        
        # Bind textures to texture slots
        self.scene_fbo.color_texture.use(0)
        self.blend_shader.set_uniform("u_scene_tex", 0)
        
        self.blur_fbo_v.color_texture.use(1)
        self.blend_shader.set_uniform("u_bloom_tex", 1)
        
        self.quad_vao.render(moderngl.TRIANGLES)
        
        # Re-enable alpha blending for standard frames
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

    def _release_fbos(self) -> None:
        """Release framebuffer memory blocks."""
        if self.scene_fbo: self.scene_fbo.release()
        if self.bright_fbo: self.bright_fbo.release()
        if self.blur_fbo_h: self.blur_fbo_h.release()
        if self.blur_fbo_v: self.blur_fbo_v.release()

    def release(self) -> None:
        """Deallocate all pipelines, geometry buffers, and shaders."""
        self._release_fbos()
        if self.quad_vao: self.quad_vao.release()
        if self.quad_vbo: self.quad_vbo.release()
        if self.threshold_shader: self.threshold_shader.release()
        if self.blur_shader: self.blur_shader.release()
        if self.blend_shader: self.blend_shader.release()
        logger.info("Post-processing pipeline GPU resources released.")
