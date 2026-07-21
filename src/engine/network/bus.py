from typing import Dict, List, Callable, Any
from src.engine.utils.logger import setup_logger

logger = setup_logger("TelemetryBus")

class TelemetryBus:
    """Decoupled publish/subscribe bus for engine telemetry events."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Subscribe a handler callback to a specific telemetry event topic."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """Unsubscribe a handler callback from a topic."""
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, payload: Any) -> None:
        """Publish payload to all subscribed callbacks."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"Error executing callback for event '{event_type}': {e}")
