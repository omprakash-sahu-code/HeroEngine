from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, Any, List
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest

class ModuleState(IntEnum):
    """Lifecycle states for HeroModule instances."""
    UNLOADED = 0
    LOADED = 1
    INITIALIZED = 2
    ACTIVE = 3
    RELEASING = 4

class HeroModule(ABC):
    """Abstract Base Class defining the lifecycle and integration API

    for all Hero modules in HeroEngine.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the hero module with its dynamic configurations.

        Args:
            config: A dictionary of configuration options specific to this module.
        """
        self.config = config
        self.state = ModuleState.LOADED

    @property
    def is_active(self) -> bool:
        """Returns True if module is currently in ACTIVE state."""
        return self.state == ModuleState.ACTIVE

    @property
    def is_initialized(self) -> bool:
        """Returns True if module has been initialized."""
        return self.state in (ModuleState.INITIALIZED, ModuleState.ACTIVE)

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the developer-friendly name of the module.

        Returns:
            str: Module name identifier (e.g., 'sorcerer', 'iron').
        """
        pass

    @property
    def version(self) -> str:
        """Returns the module semantic version. Default: '1.0.0'."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Returns a brief description of module capabilities."""
        return "HeroEngine Plugin Module"

    @property
    def author(self) -> str:
        """Returns the module author/creator."""
        return "HeroEngine Community"

    @property
    def icon(self) -> str:
        """Returns relative path or name of module icon asset."""
        return "icon.png"

    @abstractmethod
    def initialize(self) -> None:
        """Called once when the engine instantiates/prepares this module."""
        pass

    def on_activate(self) -> None:
        """Called when this module becomes the active module receiving updates/inputs.

        Can be overridden by subclasses.
        """
        self.state = ModuleState.ACTIVE

    def on_deactivate(self) -> None:
        """Called when another module is activated, putting this module into background.

        Can be overridden by subclasses.
        """
        if self.state == ModuleState.ACTIVE:
            self.state = ModuleState.INITIALIZED

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
        """Releases and cleans up allocated module CPU/GPU resources."""
        self.state = ModuleState.UNLOADED
