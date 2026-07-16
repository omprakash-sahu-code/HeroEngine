import os
import numpy as np
import moderngl
from typing import Tuple, List, Dict, Any
from src.engine.utils.logger import setup_logger
from src.engine.rendering.shader import ShaderProgram
from src.engine.rendering.request import EffectRequest

logger = setup_logger("Renderer")

class Renderer:
    """Manages the ModernGL rendering context, compiles VFX shaders,

    maintains shape buffers, and draws high-level EffectRequest collections.
    """

    def __init__(self, particle_limit: int = 5000):
        self.ctx = None
        self.particle_limit = particle_limit
        
        # Shader programs
        self.orb_shader = None
        self.shield_shader = None
        self.particles_shader = None
        
        # Vertex arrays
        self.billboard_vao = None
        self.billboard_vbo = None
        self.particle_vao = None
        self.particle_vbo = None
        
        self._initialize_context()
        self._initialize_resources()

    def _initialize_context(self) -> None:
        """Create or detect the active OpenGL/ModernGL context."""
        try:
            self.ctx = moderngl.create_context()
            logger.info(f"ModernGL context created. OpenGL Version: {self.ctx.info['GL_VERSION']}")
            
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
            
            # Enable point size modification in shaders (vital for point sprites)
            self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        except Exception as e:
            logger.critical(f"Failed to initialize ModernGL context: {e}")
            raise e

    def _initialize_resources(self) -> None:
        """Load and compile all system shaders, creating drawing structures."""
        shader_dir = os.path.join(os.path.dirname(__file__), "shaders")
        
        # 1. Compile Shaders
        try:
            # Billboard vertex shader shared by Orb and Shield
            billboard_vert = os.path.join(shader_dir, "billboard.vert")
            
            self.orb_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "orb.frag")
            )
            logger.info("Compiled Orb shaders successfully.")
            
            self.shield_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "shield.frag")
            )
            logger.info("Compiled Shield shaders successfully.")
            
            self.particles_shader = ShaderProgram(
                self.ctx, 
                os.path.join(shader_dir, "particles.vert"), 
                os.path.join(shader_dir, "particles.frag")
            )
            logger.info("Compiled Particle shaders successfully.")
        except Exception as e:
            logger.critical(f"Failed compiling VFX shaders: {e}")
            raise e

        # 2. Set up Shared Billboard Unit Quad (local coords: X, Y in [-1, 1], U, V in [0, 1])
        quad_vertices = np.array([
            -1.0, -1.0,  0.0, 0.0, # Bottom-Left
             1.0, -1.0,  1.0, 0.0, # Bottom-Right
            -1.0,  1.0,  0.0, 1.0, # Top-Left
            
            -1.0,  1.0,  0.0, 1.0, # Top-Left
             1.0, -1.0,  1.0, 0.0, # Bottom-Right
             1.0,  1.0,  1.0, 1.0, # Top-Right
        ], dtype='f4')
        
        self.billboard_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.billboard_vao = self.ctx.vertex_array(
            self.orb_shader.program, # Either program works since attributes match
            [(self.billboard_vbo, '2f 2f', 'in_position', 'in_texcoord')]
        )

        # 3. Set up dynamic vertex array for Point Particles
        # Each particle has: position (2f), color/alpha (4f)
        self.particle_vbo = self.ctx.buffer(reserve=self.particle_limit * 6 * 4) # 6 floats per point
        self.particle_vao = self.ctx.vertex_array(
            self.particles_shader.program,
            [(self.particle_vbo, '2f 4f', 'in_position', 'in_color')]
        )

    def clear(self, color: Tuple[float, float, float, float] = (0.1, 0.1, 0.1, 1.0)) -> None:
        """Clear framebuffer target."""
        if self.ctx:
            self.ctx.clear(*color)

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Update rendering viewport."""
        if self.ctx:
            self.ctx.viewport = (x, y, width, height)

    def set_blend_mode_additive(self) -> None:
        """Additive blending for glowing energy visuals."""
        if self.ctx:
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE)

    def set_blend_mode_alpha(self) -> None:
        """Standard alpha transparency blending."""
        if self.ctx:
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

    def draw_effects(self, requests: List[EffectRequest], aspect: float, time_elapsed: float) -> None:
        """Process and render high-level EffectRequest commands.

        Args:
            requests: List of drawing requests generated by the active module.
            aspect: Viewport aspect ratio correction factor (width / height).
            time_elapsed: Total running time in seconds.
        """
        for req in requests:
            if req.effect_type == "orb":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.18)
                color = req.data.get("color", (1.0, 0.45, 0.08))
                
                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                
                self.orb_shader.use()
                self.orb_shader.set_uniform("u_center", center)
                self.orb_shader.set_uniform("u_radius", radius)
                self.orb_shader.set_uniform("u_aspect", aspect)
                self.orb_shader.set_uniform("u_color", color)
                self.orb_shader.set_uniform("u_time", time_elapsed)
                self.orb_shader.set_uniform("u_rotation", 0.0)
                
                # Bind quad vertex layout and render
                self.billboard_vao.render(moderngl.TRIANGLES)
                
            elif req.effect_type == "shield":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.45)
                color = req.data.get("color", (1.0, 0.45, 0.08))
                rotation = req.data.get("rotation", 0.0)
                
                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                
                self.shield_shader.use()
                self.shield_shader.set_uniform("u_center", center)
                self.shield_shader.set_uniform("u_radius", radius)
                self.shield_shader.set_uniform("u_aspect", aspect)
                self.shield_shader.set_uniform("u_color", color)
                self.shield_shader.set_uniform("u_time", time_elapsed)
                self.shield_shader.set_uniform("u_rotation", rotation)
                
                self.billboard_vao.render(moderngl.TRIANGLES)
                
            elif req.effect_type == "particles":
                points_data = req.data.get("points_data", None)
                count = req.data.get("count", 0)
                base_size = req.data.get("base_size", 12.0)
                
                if points_data is not None and count > 0:
                    self.ctx.enable(moderngl.BLEND)
                    self.set_blend_mode_additive()
                    
                    self.particles_shader.use()
                    self.particles_shader.set_uniform("u_base_size", base_size)
                    
                    # Dynamically upload raw floats to the dynamic buffer
                    self.particle_vbo.write(points_data.tobytes())
                    
                    self.particle_vao.render(moderngl.POINTS, vertices=count)

    def release(self) -> None:
        """Release GPU buffers and shader links to prevent leaks."""
        if self.billboard_vao: self.billboard_vao.release()
        if self.billboard_vbo: self.billboard_vbo.release()
        if self.particle_vao: self.particle_vao.release()
        if self.particle_vbo: self.particle_vbo.release()
        if self.orb_shader: self.orb_shader.release()
        if self.shield_shader: self.shield_shader.release()
        if self.particles_shader: self.particles_shader.release()
        logger.info("Core Renderer GPU resources released cleanly.")
