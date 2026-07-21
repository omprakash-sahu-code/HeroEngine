"""Core Engine Facade and Plugin Architecture Exports."""

from src.engine.core.module_registry import ModuleRegistry
from src.engine.core.module_loader import ModuleLoader
from src.engine.core.module_manager import ModuleManager
from src.engine.network.bus import TelemetryBus
from src.engine.network.dispatcher import NetworkDispatcher

__all__ = [
    "ModuleRegistry",
    "ModuleLoader",
    "ModuleManager",
    "TelemetryBus",
    "NetworkDispatcher"
]
