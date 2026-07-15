import os
import moderngl
from typing import Dict, Any, Union
from src.engine.utils.logger import setup_logger

logger = setup_logger("Shader")

class ShaderProgram:
    """Compiles and manages uniforms of GLSL shader programs."""

    def __init__(self, ctx: moderngl.Context, vertex_path: str, fragment_path: str):
        """Args:

            ctx: Active ModernGL context.
            vertex_path: Path to vertex shader source.
            fragment_path: Path to fragment shader source.
        """
        self.ctx = ctx
        self.program = None
        self._load_and_compile(vertex_path, fragment_path)

    def _read_file(self, path: str) -> str:
        """Reads contents of a file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Shader file not found: {path}")
        with open(path, 'r') as file:
            return file.read()

    def _load_and_compile(self, vert_path: str, frag_path: str) -> None:
        """Load source files and compile into ModernGL program."""
        try:
            vertex_source = self._read_file(vert_path)
            fragment_source = self._read_file(frag_path)
            
            self.program = self.ctx.program(
                vertex_shader=vertex_source,
                fragment_shader=fragment_source
            )
            logger.info(f"Successfully compiled program (Vert: {os.path.basename(vert_path)}, Frag: {os.path.basename(frag_path)})")
        except Exception as e:
            logger.error(f"Failed to compile shader program: {e}")
            raise e

    def use(self) -> None:
        """Currently a placeholder since ModernGL handles active binding

        automatically upon draw execution, but keeps standard APIs clear.
        """
        pass

    def set_uniform(self, name: str, value: Any) -> None:
        """Sets a uniform value by name.

        Args:
            name: Uniform variable name.
            value: Value to set (scalar, tuple, or bytes).
        """
        if not self.program:
            return
            
        if name not in self.program:
            # Silence warning if the optimizer compiled out the uniform
            return
            
        try:
            self.program[name].value = value
        except Exception as e:
            logger.warning(f"Failed to set uniform '{name}' on program: {e}")

    def release(self) -> None:
        """Release program memory."""
        if self.program:
            self.program.release()
            self.program = None
