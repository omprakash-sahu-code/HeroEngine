import os
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from src.engine.utils.logger import setup_logger

logger = setup_logger("SystemMetrics")

class SystemMetricsProvider(ABC):
    """Abstract interface for hardware resource metrics providers."""

    @abstractmethod
    def get_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        """Samples hardware metrics.

        Returns:
            Tuple[Optional[float], Optional[float]]: (cpu_percent, memory_mb).
            Values are None if hardware load monitoring is unavailable.
        """
        pass

class NullSystemMetricsProvider(SystemMetricsProvider):
    """Silent null provider returning None for system metrics."""

    def get_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        return (None, None)

class PsutilProvider(SystemMetricsProvider):
    """System metrics provider using psutil library."""

    def __init__(self):
        self._process = None
        try:
            import psutil
            self._process = psutil.Process(os.getpid())
            # Warm up cpu_percent calculation
            self._process.cpu_percent()
        except ImportError:
            logger.info("psutil library not installed. System CPU/RAM metrics disabled (returning None).")
        except Exception as e:
            logger.warning(f"Failed to initialize psutil process monitor: {e}")

    def get_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        if self._process is None:
            return (None, None)
        try:
            cpu = self._process.cpu_percent(interval=None)
            mem_info = self._process.memory_info()
            mem_mb = mem_info.rss / (1024.0 * 1024.0)
            return (float(cpu), float(mem_mb))
        except Exception as e:
            logger.warning(f"Error sampling psutil system metrics: {e}")
            return (None, None)

def create_system_metrics_provider() -> SystemMetricsProvider:
    """Factory creating the best available SystemMetricsProvider."""
    provider = PsutilProvider()
    if provider._process is not None:
        return provider
    return NullSystemMetricsProvider()
