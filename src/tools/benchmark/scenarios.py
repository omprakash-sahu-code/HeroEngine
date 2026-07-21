import gc
import json
import time
import numpy as np
from typing import List

from src.tools.benchmark.base import BenchmarkScenario
from src.tools.benchmark.models import (
    BenchmarkConfig, ScenarioResult, calculate_percentiles
)
from src.engine.gestures.recognizer import GestureRecognizer
from src.engine.network.models import TelemetryFrame
from src.engine.network.osc_transport import OSCTransport
from src.engine.network.websocket_transport import WebSocketTransport
from src.engine.network.bus import TelemetryBus

class VisionBenchmark(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "vision"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        try:
            # Synthetic frame simulation (640x480 RGB)
            synthetic_frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Warm-up phase
            warmup_end = time.perf_counter() + config.warmup_seconds
            while time.perf_counter() < warmup_end:
                _ = synthetic_frame.mean()

            # Measurement phase
            latencies_ms: List[float] = []
            measure_end = time.perf_counter() + config.duration_seconds

            while time.perf_counter() < measure_end:
                t0 = time.perf_counter()
                # Simulate frame preprocessing & landmark spatial projection
                _ = np.linalg.norm(synthetic_frame)
                t1 = time.perf_counter()
                latencies_ms.append((t1 - t0) * 1000.0)

            return ScenarioResult(
                scenario_name=self.name,
                status="SUCCESS",
                metrics={
                    "frame_processing_latency_ms": calculate_percentiles(latencies_ms).to_dict()
                },
                custom_info={"sample_count": len(latencies_ms)}
            )
        except Exception as e:
            return ScenarioResult(scenario_name=self.name, status="FAILED", error_message=str(e))

class GestureBenchmark(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "gesture"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        try:
            recognizer = GestureRecognizer()
            raw_landmarks = [(0.5, 0.5, 0.0)] * 21
            raw_landmarks[4] = (0.2, 0.2, 0.0)
            raw_landmarks[8] = (0.22, 0.22, 0.0)

            # Warm-up phase
            warmup_end = time.perf_counter() + config.warmup_seconds
            while time.perf_counter() < warmup_end:
                _ = recognizer.recognize(raw_landmarks)

            # Measurement phase
            latencies_ms: List[float] = []
            measure_end = time.perf_counter() + config.duration_seconds

            while time.perf_counter() < measure_end:
                t0 = time.perf_counter()
                _ = recognizer.recognize(raw_landmarks)
                t1 = time.perf_counter()
                latencies_ms.append((t1 - t0) * 1000.0)

            return ScenarioResult(
                scenario_name=self.name,
                status="SUCCESS",
                metrics={
                    "classification_latency_ms": calculate_percentiles(latencies_ms).to_dict()
                },
                custom_info={"sample_count": len(latencies_ms)}
            )
        except Exception as e:
            return ScenarioResult(scenario_name=self.name, status="FAILED", error_message=str(e))

class RenderingBenchmark(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "render"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        try:
            metrics_map = {}

            for particle_count in config.particle_counts:
                # Warm-up phase for particle buffer allocation
                particles = np.random.randn(particle_count, 4).astype(np.float32)
                warmup_end = time.perf_counter() + config.warmup_seconds
                while time.perf_counter() < warmup_end:
                    particles += 0.01

                # Measurement phase
                latencies_ms: List[float] = []
                measure_end = time.perf_counter() + (config.duration_seconds / len(config.particle_counts))

                while time.perf_counter() < measure_end:
                    t0 = time.perf_counter()
                    # Simulate GPU compute/CPU update loop
                    particles[:, :3] += particles[:, 3:] * 0.016
                    t1 = time.perf_counter()
                    latencies_ms.append((t1 - t0) * 1000.0)

                metric_key = f"particle_update_latency_{particle_count}_ms"
                metrics_map[metric_key] = calculate_percentiles(latencies_ms).to_dict()

            return ScenarioResult(
                scenario_name=self.name,
                status="SUCCESS",
                metrics=metrics_map,
                custom_info={"particle_counts_tested": config.particle_counts}
            )
        except Exception as e:
            return ScenarioResult(scenario_name=self.name, status="FAILED", error_message=str(e))

class NetworkingBenchmark(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "network"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        try:
            bus = TelemetryBus()
            osc_transport = OSCTransport()
            ws_transport = WebSocketTransport()

            frame = TelemetryFrame(
                timestamp=time.time(),
                frame_number=100,
                hands={"right": {"position": [0.1, 0.2, 0.3]}},
                gestures={"right": "PINCH"},
                module="iron",
                camera={"offset_x": 0.0, "offset_y": 0.0},
                fps=60.0
            )

            # Warm-up phase
            warmup_end = time.perf_counter() + config.warmup_seconds
            while time.perf_counter() < warmup_end:
                _ = osc_transport.serialize(frame)
                _ = ws_transport.serialize(frame)

            # Measurement phase: Serialization & Enqueue
            osc_latencies_ms: List[float] = []
            ws_latencies_ms: List[float] = []
            enqueue_latencies_ms: List[float] = []

            measure_end = time.perf_counter() + config.duration_seconds
            while time.perf_counter() < measure_end:
                # OSC byte serialization
                t0 = time.perf_counter()
                _ = osc_transport.serialize(frame)
                t1 = time.perf_counter()
                osc_latencies_ms.append((t1 - t0) * 1000.0)

                # WS JSON serialization
                t2 = time.perf_counter()
                _ = ws_transport.serialize(frame)
                t3 = time.perf_counter()
                ws_latencies_ms.append((t3 - t2) * 1000.0)

                # Bus enqueue latency
                t4 = time.perf_counter()
                bus.publish(frame)
                t5 = time.perf_counter()
                enqueue_latencies_ms.append((t5 - t4) * 1000.0)

            return ScenarioResult(
                scenario_name=self.name,
                status="SUCCESS",
                metrics={
                    "osc_serialization_latency_ms": calculate_percentiles(osc_latencies_ms).to_dict(),
                    "json_serialization_latency_ms": calculate_percentiles(ws_latencies_ms).to_dict(),
                    "bus_enqueue_latency_ms": calculate_percentiles(enqueue_latencies_ms).to_dict()
                },
                custom_info={"packets_profiled": len(osc_latencies_ms)}
            )
        except Exception as e:
            return ScenarioResult(scenario_name=self.name, status="FAILED", error_message=str(e))

class MemoryBenchmark(BenchmarkScenario):
    @property
    def name(self) -> str:
        return "memory"

    def run(self, config: BenchmarkConfig) -> ScenarioResult:
        try:
            gc.collect()

            # Measure garbage collection overhead and synthetic allocation rates
            gc_pause_latencies_ms: List[float] = []
            measure_end = time.perf_counter() + config.duration_seconds

            dummy_allocations = []
            while time.perf_counter() < measure_end:
                # Allocation simulation
                dummy_allocations.append([0.0] * 1000)
                if len(dummy_allocations) > 50:
                    t0 = time.perf_counter()
                    dummy_allocations.clear()
                    gc.collect()
                    t1 = time.perf_counter()
                    gc_pause_latencies_ms.append((t1 - t0) * 1000.0)

            return ScenarioResult(
                scenario_name=self.name,
                status="SUCCESS",
                metrics={
                    "gc_pause_latency_ms": calculate_percentiles(gc_pause_latencies_ms).to_dict()
                },
                custom_info={"gc_collections_run": len(gc_pause_latencies_ms)}
            )
        except Exception as e:
            return ScenarioResult(scenario_name=self.name, status="FAILED", error_message=str(e))
