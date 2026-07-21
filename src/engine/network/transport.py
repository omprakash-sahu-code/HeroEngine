from abc import ABC, abstractmethod
from src.engine.network.models import TelemetryFrame

class Transport(ABC):
    """Abstract interface defining interchangeable telemetry network transports."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Transport identifier name."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Return True if transport server/socket is running."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Initialize and start transport worker/server."""
        pass

    @abstractmethod
    def send(self, frame: TelemetryFrame) -> None:
        """Serialize and transmit a telemetry frame."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Gracefully shut down transport worker/server."""
        pass
