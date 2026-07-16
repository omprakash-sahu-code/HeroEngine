import os
import random
import numpy as np
import moderngl
from typing import Tuple
from src.engine.rendering.shader import ShaderProgram
from src.engine.utils.logger import setup_logger

logger = setup_logger("GPUParticleSystem")

class ParticleSimulationMode:
    """Predefined simulation behaviors for the GPU particle kinematic engine."""
    BALLISTIC = 0.0  # Default: outward velocities, gravity, and drag
    SPIRAL = 1.0     # Inward spiral vortex towards the birth centroid


class GPUParticleSystem:
    """High-performance GPU instanced particle system.

    Calculates physics (drag, gravity, size, color fade) in shaders.
    Uses a GPU circular ring buffer to manage particle instances.
    """

    def __init__(self, ctx: moderngl.Context, limit: int = 10000):
        self.ctx = ctx
        self.limit = limit
        self.cursor = 0  # Ring buffer pointer

        self.shader = None
        self.quad_vbo = None
        self.particle_vbo = None
        self.vao = None

        self._initialize_resources()

    def _initialize_resources(self) -> None:
        """Compile GPU shaders and configure vertex arrays."""
        # 1. Compile instanced particle shader
        shader_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shaders")
        vert_path = os.path.join(shader_dir, "gpu_particles.vert")
        frag_path = os.path.join(shader_dir, "gpu_particles.frag")

        try:
            self.shader = ShaderProgram(self.ctx, vert_path, frag_path)
            logger.info("Compiled GPU Particle shaders successfully.")
        except Exception as e:
            logger.critical(f"Failed compiling GPU instanced particle shaders: {e}")
            raise e

        # 2. Quad geometry VBO (Triangle Strip for billboard rendering)
        # 4 vertices: Local coords X, Y in [-0.5, 0.5]
        quad_vertices = np.array([
            -0.5, -0.5,  # Bottom-Left
             0.5, -0.5,  # Bottom-Right
            -0.5,  0.5,  # Top-Left
             0.5,  0.5,  # Top-Right
        ], dtype='f4')
        self.quad_vbo = self.ctx.buffer(quad_vertices.tobytes())

        # 3. Particle instance VBO (pre-allocate GPU ring buffer)
        # Format per instance:
        # spawn_pos (2f), spawn_vel (2f), birth_time (1f), lifetime (1f), color (3f), simulation_mode (1f) -> 10 floats = 40 bytes per particle
        self.struct_size = 40
        self.particle_vbo = self.ctx.buffer(reserve=self.limit * self.struct_size)

        # Initialize GPU buffer to 0 (so initial state particles are immediately dead)
        zero_data = np.zeros(self.limit * 10, dtype='f4')
        self.particle_vbo.write(zero_data.tobytes())

        # 4. Create VAO mapping quad vertex coordinates (vertex attribute)
        # and particle structures (instance attributes indicated by '/i')
        self.vao = self.ctx.vertex_array(
            self.shader.program,
            [
                (self.quad_vbo, '2f', 'in_quad_pos'),
                (self.particle_vbo, '2f 2f 1f 1f 3f 1f /i', 'in_birth_pos', 'in_birth_vel', 'in_birth_time', 'in_lifetime', 'in_color', 'in_simulation_mode')
            ]
        )
        logger.info(f"Initialized GPUParticleSystem with limit: {self.limit}")

    def emit(
        self,
        center: Tuple[float, float],
        count: int,
        color: Tuple[float, float, float],
        speed: float,
        current_time: float,
        mode: float = ParticleSimulationMode.BALLISTIC
    ) -> None:
        """Spawn new particles inside the GPU ring-buffer by writing spawn specs.

        Args:
            center: NDC coordinate (x, y).
            count: Number of particles to spawn.
            color: Tuple RGB color.
            speed: Velocity coefficient or angle.
            current_time: Current simulation elapsed time in seconds.
            mode: Motion trajectory simulation mode constant from ParticleSimulationMode.
        """
        if count <= 0:
            return

        # Cap count to limit
        count = min(count, self.limit)

        # Generate particle instance structures on CPU
        # Structure layout: [x, y, vx, vy, birth_time, lifetime, r, g, b, simulation_mode] (10 floats)
        particles_data = np.zeros(count * 10, dtype='f4')

        for i in range(count):
            if mode == ParticleSimulationMode.SPIRAL:
                # Store the randomized starting angle in the vx field for the shader spiral equation
                vx = random.uniform(0.0, 2.0 * np.pi)
                vy = 0.0
                lifetime = random.uniform(0.7, 1.1)
            else:
                angle = random.uniform(0, 2 * np.pi)
                r_speed = random.uniform(0.1, speed)
                vx = r_speed * np.cos(angle)
                vy = r_speed * np.sin(angle)
                lifetime = random.uniform(0.4, 0.9)
            
            idx = i * 10
            particles_data[idx]     = center[0]
            particles_data[idx + 1] = center[1]
            particles_data[idx + 2] = vx
            particles_data[idx + 3] = vy
            particles_data[idx + 4] = current_time
            particles_data[idx + 5] = lifetime
            particles_data[idx + 6] = color[0]
            particles_data[idx + 7] = color[1]
            particles_data[idx + 8] = color[2]
            particles_data[idx + 9] = mode

        raw_bytes = particles_data.tobytes()

        # Handle ring-buffer wrap-around writing
        space_left = self.limit - self.cursor
        if count <= space_left:
            # Write in one chunk
            self.particle_vbo.write(raw_bytes, offset=self.cursor * self.struct_size)
            self.cursor = (self.cursor + count) % self.limit
        else:
            # Split into two chunks (end of buffer & start of buffer)
            first_chunk_size = space_left
            second_chunk_size = count - space_left

            first_bytes = raw_bytes[:first_chunk_size * self.struct_size]
            second_bytes = raw_bytes[first_chunk_size * self.struct_size:]

            self.particle_vbo.write(first_bytes, offset=self.cursor * self.struct_size)
            self.particle_vbo.write(second_bytes, offset=0)
            self.cursor = second_chunk_size

    def draw(self, aspect: float, current_time: float) -> None:
        """Execute OpenGL instanced draw command to render particles."""
        self.shader.use()
        self.shader.set_uniform("u_time", current_time)
        self.shader.set_uniform("u_aspect", aspect)

        # Draw call using Triangle Strip with instancing
        self.vao.render(moderngl.TRIANGLE_STRIP, instances=self.limit)

    def release(self) -> None:
        """Release OpenGL buffer targets."""
        if self.quad_vbo: self.quad_vbo.release()
        if self.particle_vbo: self.particle_vbo.release()
        if self.vao: self.vao.release()
        if self.shader: self.shader.release()
        logger.info("GPUParticleSystem resources released cleanly.")
