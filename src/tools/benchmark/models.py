import datetime
import math
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

@dataclass
class SystemMetadata:
    platform: str
    python_version: str
    git_commit: str
    timestamp: str
    cpu_info: str
    gpu_info: str

    @classmethod
    def capture(cls) -> 'SystemMetadata':
        git_commit = "unknown"
        try:
            res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0:
                git_commit = res.stdout.strip()
        except Exception:
            pass

        return cls(
            platform=f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            python_version=sys.version.split()[0],
            git_commit=git_commit,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cpu_info=platform.processor() or "Unknown CPU",
            gpu_info="ModernGL / OpenGL Hardware Accelerated"
        )

@dataclass
class PercentileMetrics:
    min: float
    max: float
    mean: float
    median_p50: float
    p95: float
    p99: float
    std_dev: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

def calculate_percentiles(samples: List[float]) -> PercentileMetrics:
    """Calculate min, max, mean, P50, P95, P99, and std_dev from sample data."""
    if not samples:
        return PercentileMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    sorted_samples = sorted(samples)
    n = len(sorted_samples)

    def get_percentile(p: float) -> float:
        idx = (p / 100.0) * (n - 1)
        lower = math.floor(idx)
        upper = math.ceil(idx)
        weight = idx - lower
        if lower == upper:
            return sorted_samples[int(idx)]
        return sorted_samples[lower] * (1.0 - weight) + sorted_samples[upper] * weight

    mean_val = sum(sorted_samples) / n
    variance = sum((x - mean_val) ** 2 for x in sorted_samples) / n if n > 1 else 0.0
    std_dev_val = math.sqrt(variance)

    return PercentileMetrics(
        min=round(sorted_samples[0], 4),
        max=round(sorted_samples[-1], 4),
        mean=round(mean_val, 4),
        median_p50=round(get_percentile(50), 4),
        p95=round(get_percentile(95), 4),
        p99=round(get_percentile(99), 4),
        std_dev=round(std_dev_val, 4)
    )

@dataclass
class ScenarioResult:
    scenario_name: str
    status: str  # "SUCCESS" or "FAILED"
    metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    error_message: Optional[str] = None
    custom_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BenchmarkConfig:
    duration_seconds: float = 3.0
    warmup_seconds: float = 1.0
    particle_counts: List[int] = field(default_factory=lambda: [1000, 5000, 10000])
    headless: bool = True
    scenarios: List[str] = field(default_factory=lambda: ["vision", "gesture", "render", "network", "memory"])

@dataclass
class BenchmarkResult:
    metadata: SystemMetadata
    config: BenchmarkConfig
    scenarios: Dict[str, ScenarioResult] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "config": asdict(self.config),
            "scenarios": {k: asdict(v) for k, v in self.scenarios.items()}
        }
