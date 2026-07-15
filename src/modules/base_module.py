from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest

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
    def initialize(self) -> None:
        """Called once when the engine activates this module.

        Set up initial state parameters and CPU components.
        """
        pass

    @abstractmethod
    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Processes debounced hand states and coordinate tracking parameters.

        Args:
            active_hands: A dictionary mapping hand label ('Left'/'Right') to HandState instances.
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advances internal logic, particle systems, and animation timers.

        Args:
            dt: Time elapsed since the last frame in seconds.
        """
        pass

    @abstractmethod
    def get_render_requests(self) -> List[EffectRequest]:
        """Returns a list of high-level rendering requests representing active spell effects.

        Returns:
            List[EffectRequest]: Emitter commands processed by the core renderer.
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Releases and cleans up allocated module CPU resources."""
        pass

