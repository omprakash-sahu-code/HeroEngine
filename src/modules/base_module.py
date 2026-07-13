from abc import ABC, abstractmethod
from typing import Dict, Any

class HeroModule(ABC):
    """Abstract Base Class defining the life-cycle and integration API

    for all Hero modules in HeroEngine.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the hero module with its dynamic configurations.

        Args:
            config: A dictionary of configuration options specific to this module.
        """
        self.config = config
        self.is_active = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the developer-friendly name of the module.

        Returns:
            str: Module name identifier (e.g., 'sorcerer', 'iron').
        """
        pass

    @abstractmethod
    def initialize(self, ctx) -> None:
        """Called once when the engine activates this module.

        Initializes GPU resources, compiles shaders, and loads textures.

        Args:
            ctx: The ModernGL context instance.
        """
        pass

    @abstractmethod
    def update(self, landmarks: Dict[str, Any], delta_time: float) -> None:
        """Processes raw coordinates and gesture outputs.

        Updates internal state, animations, physics, and particle controllers.

        Args:
            landmarks: A dictionary containing hand, pose, and face landmark groups.
            delta_time: Time elapsed since the last frame in seconds.
        """
        pass

    @abstractmethod
    def render(self, ctx) -> None:
        """Performs specific ModernGL draw calls to render the module's VFX.

        Args:
            ctx: The ModernGL context instance.
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases and cleans up all allocated OpenGL textures, buffers,

        and programs to avoid resource leaks when the module is swapped or closed.
        """
        pass
