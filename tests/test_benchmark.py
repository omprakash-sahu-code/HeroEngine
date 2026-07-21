import os
import unittest
from typing import Dict, Any

from src.tools.benchmark.models import (
    BenchmarkConfig, BenchmarkResult, ScenarioResult, SystemMetadata, calculate_percentiles
)
from src.tools.benchmark.base import BenchmarkScenario
from src.tools.benchmark.runner import BenchmarkRunner

class FaultyScenario(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "faulty"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        raise ValueError("Simulated benchmark failure!")

class DummyScenario(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "dummy"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        return ScenarioResult(
            scenario_name=self.name,
            status="SUCCESS",
            metrics={"dummy_metric_ms": {"min": 1.0, "max": 2.0, "mean": 1.5, "median_p50": 1.5, "p95": 1.9, "p99": 1.99, "std_dev": 0.2}}
        )

class TestBenchmarkSystem(unittest.TestCase):

    def test_percentile_calculations(self):
        samples = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        res = calculate_percentiles(samples)

        self.assertEqual(res.min, 1.0)
        self.assertEqual(res.max, 10.0)
        self.assertEqual(res.mean, 5.5)
        self.assertAlmostEqual(res.median_p50, 5.5, delta=0.5)
        self.assertTrue(res.p95 > res.median_p50)
        self.assertTrue(res.p99 >= res.p95)

    def test_system_metadata_capture(self):
        meta = SystemMetadata.capture()
        self.assertTrue(len(meta.platform) > 0)
        self.assertTrue(len(meta.python_version) > 0)

    def test_runner_fault_isolation(self):
        runner = BenchmarkRunner()
        runner.register_scenario(FaultyScenario())
        runner.register_scenario(DummyScenario())

        config = BenchmarkConfig(
            duration_seconds=0.1,
            warmup_seconds=0.05,
            scenarios=["faulty", "dummy"]
        )

        res = runner.run(config)
        self.assertIn("faulty", res.scenarios)
        self.assertIn("dummy", res.scenarios)

        self.assertEqual(res.scenarios["faulty"].status, "FAILED")
        self.assertIn("Simulated benchmark failure", res.scenarios["faulty"].error_message)
        self.assertEqual(res.scenarios["dummy"].status, "SUCCESS")

    def test_empty_benchmark_run(self):
        runner = BenchmarkRunner()
        config = BenchmarkConfig(scenarios=[])
        res = runner.run(config)
        self.assertEqual(len(res.scenarios), 0)

    def test_regression_comparison_logic(self):
        runner = BenchmarkRunner()
        baseline = {
            "scenarios": {
                "dummy": {
                    "status": "SUCCESS",
                    "metrics": {
                        "dummy_metric_ms": {"p95": 2.0}
                    }
                }
            }
        }

        meta = SystemMetadata.capture()
        config = BenchmarkConfig(scenarios=["dummy"])
        scenarios_map = {"dummy": DummyScenario().run(config)}
        curr_res = BenchmarkResult(metadata=meta, config=config, scenarios=scenarios_map)

        comp_report = runner.compare_results(curr_res, baseline)
        self.assertIn("dummy_metric_ms", comp_report)
        self.assertIn("IMPROVED", comp_report)

if __name__ == "__main__":
    unittest.main()
