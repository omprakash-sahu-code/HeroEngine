import json
from typing import Dict, List, Optional, Any

from src.tools.benchmark.base import BenchmarkScenario
from src.tools.benchmark.models import (
    BenchmarkConfig, BenchmarkResult, ScenarioResult, SystemMetadata
)
from src.tools.benchmark.scenarios import (
    VisionBenchmark, GestureBenchmark, RenderingBenchmark,
    NetworkingBenchmark, MemoryBenchmark
)

class BenchmarkRunner:
    """Orchestrates benchmark scenario execution, metadata capture, report rendering, and regression comparison."""

    def __init__(self):
        self._registered_scenarios: Dict[str, BenchmarkScenario] = {
            "vision": VisionBenchmark(),
            "gesture": GestureBenchmark(),
            "render": RenderingBenchmark(),
            "network": NetworkingBenchmark(),
            "memory": MemoryBenchmark(),
        }

    def register_scenario(self, scenario: BenchmarkScenario) -> None:
        """Register a custom benchmark scenario plugin."""
        self._registered_scenarios[scenario.name] = scenario

    def run(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run requested benchmark scenarios cleanly with fault isolation.

        Args:
            config: Benchmark configuration options.

        Returns:
            BenchmarkResult: Aggregated system benchmark results.
        """
        metadata = SystemMetadata.capture()
        scenario_results: Dict[str, ScenarioResult] = {}

        for scenario_name in config.scenarios:
            if scenario_name in self._registered_scenarios:
                scenario = self._registered_scenarios[scenario_name]
                try:
                    result = scenario.run(config)
                    scenario_results[scenario_name] = result
                except Exception as e:
                    scenario_results[scenario_name] = ScenarioResult(
                        scenario_name=scenario_name,
                        status="FAILED",
                        error_message=str(e)
                    )

        return BenchmarkResult(
            metadata=metadata,
            config=config,
            scenarios=scenario_results
        )

    @staticmethod
    def generate_markdown_report(result: BenchmarkResult) -> str:
        """Generate formatted Markdown report from benchmark results."""
        res_dict = result.to_dict()
        meta = res_dict["metadata"]
        lines = [
            "# HeroEngine Benchmark Report",
            "",
            f"**Generated:** {meta['timestamp']}  ",
            f"**Git Commit:** `{meta['git_commit']}` | **Python:** `{meta['python_version']}` | **Platform:** `{meta['platform']}`  ",
            f"**CPU:** {meta['cpu_info']} | **GPU:** {meta['gpu_info']}  ",
            "",
            "## Scenario Metrics Summary",
            ""
        ]

        for s_name, s_data in res_dict["scenarios"].items():
            lines.append(f"### Scenario: `{s_name.upper()}` (Status: {s_data['status']})")
            if s_data["status"] == "FAILED":
                lines.append(f"> [!WARNING]\n> Failure Reason: {s_data.get('error_message')}\n")
                continue

            lines.append("| Metric | Min (ms) | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | StdDev |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for m_name, m_val in s_data.get("metrics", {}).items():
                lines.append(
                    f"| `{m_name}` | {m_val['min']} | {m_val['mean']} | {m_val['median_p50']} | "
                    f"{m_val['p95']} | {m_val['p99']} | {m_val['max']} | {m_val['std_dev']} |"
                )
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def compare_results(current_result: BenchmarkResult, baseline_dict: Dict[str, Any]) -> str:
        """Compare current benchmark metrics against a baseline JSON dictionary."""
        curr_dict = current_result.to_dict()
        lines = [
            "# Performance Regression Comparison Report",
            "",
            "| Scenario | Metric | Baseline P95 (ms) | Current P95 (ms) | Delta (%) | Status |",
            "|---|---|---|---|---|---|"
        ]

        curr_scenarios = curr_dict.get("scenarios", {})
        base_scenarios = baseline_dict.get("scenarios", {})

        for s_name, s_curr in curr_scenarios.items():
            if s_curr.get("status") != "SUCCESS":
                continue
            s_base = base_scenarios.get(s_name, {})
            if s_base.get("status") != "SUCCESS":
                continue

            curr_metrics = s_curr.get("metrics", {})
            base_metrics = s_base.get("metrics", {})

            for m_name, curr_m in curr_metrics.items():
                if m_name in base_metrics:
                    base_p95 = base_metrics[m_name].get("p95", 0.0)
                    curr_p95 = curr_m.get("p95", 0.0)

                    if base_p95 > 0:
                        delta_pct = ((curr_p95 - base_p95) / base_p95) * 100.0
                    else:
                        delta_pct = 0.0

                    status_str = "🟢 IMPROVED" if delta_pct < -2.0 else ("🔴 SLOWER" if delta_pct > 5.0 else "⚪ STABLE")
                    lines.append(
                        f"| `{s_name}` | `{m_name}` | {base_p95:.3f} | {curr_p95:.3f} | {delta_pct:+.2f}% | {status_str} |"
                    )

        return "\n".join(lines)
