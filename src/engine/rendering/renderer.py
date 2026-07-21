import os
import numpy as np
import moderngl
from typing import Tuple, List, Dict, Any
from src.engine.utils.logger import setup_logger
from src.engine.rendering.shader import ShaderProgram
from src.engine.rendering.request import EffectRequest, CameraRequest
from src.engine.core.camera_impulse import CameraImpulse
from src.engine.utils.paths import resource_path

logger = setup_logger("Renderer")

class Renderer:
    """Manages the ModernGL rendering context, compiles VFX shaders,

    maintains shape buffers, and draws high-level EffectRequest collections.
    """

    def __init__(self, particle_limit: int = 5000, config: Dict[str, Any] = None):
        self.ctx = None
        self.particle_limit = particle_limit
        self.config = config
        
        # Shader programs
        self.orb_shader = None
        self.shield_shader = None
        # Vertex arrays
        self.billboard_vao = None
        self.billboard_vbo = None
        self.gpu_particles = None
        
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
        shader_dir = resource_path("src/engine/rendering/shaders")
        
        # 1. Compile Shaders
        try:
            billboard_vert = os.path.join(shader_dir, "billboard.vert")
            
            self.orb_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "orb.frag")
            )
            logger.info("Compiled Orb shaders successfully.")
            
            self.shield_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "shield.frag")
            )
            logger.info("Compiled Shield shaders successfully.")

            self.repulsor_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "repulsor.frag")
            )
            logger.info("Compiled Repulsor shaders successfully.")

            self.hud_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "hud.frag")
            )
            logger.info("Compiled HUD shaders successfully.")

            self.polyline_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "polyline.frag")
            )
            logger.info("Compiled Polyline shaders successfully.")

            self.lightning_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "lightning.frag")
            )
            logger.info("Compiled Lightning shaders successfully.")

            self.distortion_shader = ShaderProgram(
                self.ctx, billboard_vert, os.path.join(shader_dir, "distortion.frag")
            )
            logger.info("Compiled Distortion shaders successfully.")
        except Exception as e:
            logger.critical(f"Failed compiling VFX shaders: {e}")
            raise e

        self.camera_impulse = CameraImpulse()

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

        # 3. Set up GPU-based instanced particle system
        from src.engine.rendering.particles.gpu_particles import GPUParticleSystem
        self.gpu_particles = GPUParticleSystem(self.ctx, limit=self.particle_limit, config=self.config)

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

    def process_camera_requests(self, requests: List[CameraRequest], dt: float) -> Tuple[float, float]:
        """Process decoupled CameraRequest instances and calculate current screen shake offset."""
        for req in requests:
            if req.action == "shake":
                intensity = req.data.get("intensity", 0.05)
                duration = req.data.get("duration", 0.4)
                frequency = req.data.get("frequency", 25.0)
                self.camera_impulse.trigger_impulse(intensity=intensity, duration=duration, frequency=frequency)

        return self.camera_impulse.update(dt)

    def draw_effects(self, requests: List[EffectRequest], aspect: float, time_elapsed: float) -> None:
        """Process and render high-level EffectRequest commands.

        Args:
            requests: List of drawing requests generated by the active module.
            aspect: Viewport aspect ratio correction factor (width / height).
            time_elapsed: Total running time in seconds.
        """
        for req in requests:
            if req.effect_type == "distortion_field":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.35)
                color = req.data.get("color", (0.9, 0.1, 0.2))
                strength = req.data.get("strength", 1.0)

                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                self.distortion_shader.use()
                self.distortion_shader.set_uniform("u_center", center)
                self.distortion_shader.set_uniform("u_radius", radius)
                self.distortion_shader.set_uniform("u_aspect", aspect)
                self.distortion_shader.set_uniform("u_color", color)
                self.distortion_shader.set_uniform("u_time", time_elapsed)
                self.distortion_shader.set_uniform("u_strength", float(strength))
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "wisp_arc":
                points = req.data.get("points", [])
                color = req.data.get("color", (1.0, 0.2, 0.3))
                thickness = req.data.get("thickness", 1.2)

                if len(points) >= 2:
                    self.ctx.enable(moderngl.BLEND)
                    self.set_blend_mode_additive()
                    self.polyline_shader.use()
                    self.polyline_shader.set_uniform("u_aspect", aspect)
                    self.polyline_shader.set_uniform("u_color", color)
                    self.polyline_shader.set_uniform("u_tension", 0.2)
                    self.polyline_shader.set_uniform("u_thickness", float(thickness))

                    for i in range(len(points) - 1):
                        p1 = (points[i][0], points[i][1])
                        p2 = (points[i+1][0], points[i+1][1])
                        self.polyline_shader.set_uniform("u_p1", p1)
                        self.polyline_shader.set_uniform("u_p2", p2)
                        self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "eye_aura":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.08)
                color = req.data.get("color", (0.2, 0.8, 1.0))
                charge = req.data.get("charge", 1.0)

                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                self.lightning_shader.use()
                self.lightning_shader.set_uniform("u_center", center)
                self.lightning_shader.set_uniform("u_radius", radius)
                self.lightning_shader.set_uniform("u_aspect", aspect)
                self.lightning_shader.set_uniform("u_color", color)
                self.lightning_shader.set_uniform("u_time", time_elapsed)
                self.lightning_shader.set_uniform("u_charge", float(charge))
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "orb":
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
                
            elif req.effect_type in ("repulsor_ring", "repulsor_beam", "repulsor_flash"):
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.25)
                color = req.data.get("color", (0.2, 0.8, 1.0))
                charge = req.data.get("charge", 1.0)
                beam_end = req.data.get("beam_end", (0.0, 0.0))
                
                mode_map = {"repulsor_ring": 0, "repulsor_beam": 1, "repulsor_flash": 2}
                mode_val = mode_map[req.effect_type]
                
                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                
                self.repulsor_shader.use()
                self.repulsor_shader.set_uniform("u_center", center)
                self.repulsor_shader.set_uniform("u_radius", radius)
                self.repulsor_shader.set_uniform("u_aspect", aspect)
                self.repulsor_shader.set_uniform("u_color", color)
                self.repulsor_shader.set_uniform("u_charge", charge)
                self.repulsor_shader.set_uniform("u_time", time_elapsed)
                self.repulsor_shader.set_uniform("u_mode", mode_val)
                self.repulsor_shader.set_uniform("u_beam_end", beam_end)
                
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "hud_target":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.2)
                color = req.data.get("color", (0.1, 0.9, 1.0))
                locked = req.data.get("locked", 0.0)
                rotation = req.data.get("rotation", time_elapsed * 0.5)
                
                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                
                self.hud_shader.use()
                self.hud_shader.set_uniform("u_center", center)
                self.hud_shader.set_uniform("u_radius", radius)
                self.hud_shader.set_uniform("u_aspect", aspect)
                self.hud_shader.set_uniform("u_color", color)
                self.hud_shader.set_uniform("u_time", time_elapsed)
                self.hud_shader.set_uniform("u_locked", float(locked))
                self.hud_shader.set_uniform("u_rotation", rotation)
                
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "polyline":
                points = req.data.get("points", [])
                color = req.data.get("color", (0.9, 0.95, 1.0))
                tension = req.data.get("tension", 0.0)
                thickness = req.data.get("thickness", 1.0)

                if len(points) >= 2:
                    self.ctx.enable(moderngl.BLEND)
                    self.set_blend_mode_additive()
                    self.polyline_shader.use()
                    self.polyline_shader.set_uniform("u_aspect", aspect)
                    self.polyline_shader.set_uniform("u_color", color)
                    self.polyline_shader.set_uniform("u_tension", float(tension))
                    self.polyline_shader.set_uniform("u_thickness", float(thickness))

                    for i in range(len(points) - 1):
                        p1 = (points[i][0], points[i][1])
                        p2 = (points[i+1][0], points[i+1][1])
                        self.polyline_shader.set_uniform("u_p1", p1)
                        self.polyline_shader.set_uniform("u_p2", p2)
                        self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "web_projectile":
                start = req.data.get("start", (0.0, 0.0))
                end = req.data.get("end", (0.0, 0.0))
                color = req.data.get("color", (0.95, 0.95, 1.0))
                
                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                self.polyline_shader.use()
                self.polyline_shader.set_uniform("u_aspect", aspect)
                self.polyline_shader.set_uniform("u_color", color)
                self.polyline_shader.set_uniform("u_tension", 0.0)
                self.polyline_shader.set_uniform("u_thickness", 1.5)
                self.polyline_shader.set_uniform("u_p1", (start[0], start[1]))
                self.polyline_shader.set_uniform("u_p2", (end[0], end[1]))
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "web_splatch":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.15)
                color = req.data.get("color", (0.9, 0.95, 1.0))

                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                self.orb_shader.use()
                self.orb_shader.set_uniform("u_center", center)
                self.orb_shader.set_uniform("u_radius", radius)
                self.orb_shader.set_uniform("u_aspect", aspect)
                self.orb_shader.set_uniform("u_color", color)
                self.orb_shader.set_uniform("u_time", time_elapsed)
                self.orb_shader.set_uniform("u_rotation", 0.0)
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "web_reticle":
                center = req.data.get("center", (0.0, 0.0))
                radius = req.data.get("radius", 0.12)
                color = req.data.get("color", (0.8, 0.9, 1.0))

                self.ctx.enable(moderngl.BLEND)
                self.set_blend_mode_additive()
                self.hud_shader.use()
                self.hud_shader.set_uniform("u_center", center)
                self.hud_shader.set_uniform("u_radius", radius)
                self.hud_shader.set_uniform("u_aspect", aspect)
                self.hud_shader.set_uniform("u_color", color)
                self.hud_shader.set_uniform("u_time", time_elapsed)
                self.hud_shader.set_uniform("u_locked", 1.0)
                self.hud_shader.set_uniform("u_rotation", time_elapsed * 0.8)
                self.billboard_vao.render(moderngl.TRIANGLES)

            elif req.effect_type == "emit_particles":
                center = req.data.get("center", (0.0, 0.0))
                count = req.data.get("count", 0)
                color = req.data.get("color", (1.0, 0.5, 0.1))
                speed = req.data.get("speed", 0.6)
                mode = req.data.get("mode", 0.0) # Default to 0.0 (BALLISTIC)
                preset = req.data.get("preset", None)
                
                if count > 0:
                    self.gpu_particles.emit(
                        center=center,
                        count=count,
                        color=color,
                        speed=speed,
                        current_time=time_elapsed,
                        mode=mode,
                        preset=preset
                    )

        # 2. Automatically render active GPU particles every frame
        if self.gpu_particles:
            self.ctx.enable(moderngl.BLEND)
            self.set_blend_mode_additive()
            self.gpu_particles.draw(aspect, time_elapsed)

    def release(self) -> None:
        """Release GPU buffers and shader links to prevent leaks."""
        if self.billboard_vao: self.billboard_vao.release()
        if self.billboard_vbo: self.billboard_vbo.release()
        if self.gpu_particles: self.gpu_particles.release()
        if self.orb_shader: self.orb_shader.release()
        if self.shield_shader: self.shield_shader.release()
        if hasattr(self, "repulsor_shader") and self.repulsor_shader: self.repulsor_shader.release()
        if hasattr(self, "hud_shader") and self.hud_shader: self.hud_shader.release()
        if hasattr(self, "polyline_shader") and self.polyline_shader: self.polyline_shader.release()
        if hasattr(self, "lightning_shader") and self.lightning_shader: self.lightning_shader.release()
        if hasattr(self, "distortion_shader") and self.distortion_shader: self.distortion_shader.release()
        logger.info("Core Renderer GPU resources released cleanly.")
