from abc import ABC, abstractmethod
from src.tools.benchmark.models import BenchmarkConfig, ScenarioResult

class BenchmarkScenario(ABC):
    """Abstract base class for all plug-and-play benchmark scenarios."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique scenario name identifier (e.g. 'vision', 'render', 'network')."""
        pass

    @abstractmethod
    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        """Execute scenario workload and return compiled metrics.

        Args:
            config: Global benchmark execution configuration.

        Returns:
            ScenarioResult: Results object containing timing metrics or failure reason.
        """
        pass
