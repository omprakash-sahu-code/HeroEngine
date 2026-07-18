import unittest
import time
import threading
from src.engine.core.profiler_types import ProfileSection, ProfileSnapshot
from src.engine.core.system_metrics import NullSystemMetricsProvider, PsutilProvider
from src.engine.core.monitor import PerformanceMonitor

class TestPerformanceMonitor(unittest.TestCase):
    """Test suite for PerformanceMonitor, Profiler, system providers, and ProfileSnapshots."""

    def test_profile_snapshot_immutability(self):
        snap = ProfileSnapshot(
            frame_id=42,
            fps=60.0,
            frame_time_ms=16.6,
            latencies_ms={"post_process": 2.5},
            p95_latencies_ms={"post_process": 3.1},
            cpu_percent=None,
            memory_mb=None,
            active_module_name="sorcerer"
        )
        self.assertEqual(snap.frame_id, 42)
        self.assertIsNone(snap.cpu_percent)

        with self.assertRaises(Exception):
            snap.fps = 120.0  # Frozen dataclass immutability check

    def test_null_system_metrics_provider(self):
        provider = NullSystemMetricsProvider()
        cpu, mem = provider.get_metrics()
        self.assertIsNone(cpu)
        self.assertIsNone(mem)

    def test_context_manager_profiling_and_exception_safety(self):
        monitor = PerformanceMonitor(window_size=10, system_provider=NullSystemMetricsProvider())

        # Test context manager timing
        with monitor.profile(ProfileSection.POST_PROCESS):
            time.sleep(0.02)

        lat = monitor.get_average_latency(ProfileSection.POST_PROCESS)
        self.assertGreaterEqual(lat, 18.0)

        # Test exception safety inside context block
        try:
            with monitor.profile("failing_section"):
                time.sleep(0.01)
                raise ValueError("Simulated pipeline exception")
        except ValueError:
            pass

        # Section timing must still be recorded cleanly despite exception
        failing_lat = monitor.get_average_latency("failing_section")
        self.assertGreaterEqual(failing_lat, 8.0)

    def test_rolling_window_and_percentiles(self):
        monitor = PerformanceMonitor(window_size=10, system_provider=NullSystemMetricsProvider())

        # Simulate 15 frame ticks (exceeding window size 10)
        for i in range(15):
            monitor.tick()
            monitor.record_latency("render", float(i * 10.0))

        # Check bounded deque window size
        self.assertEqual(len(monitor._frame_times), 10)
        self.assertEqual(len(monitor._section_latencies["render"]), 10)

        snapshot = monitor.get_snapshot(active_module_name="sorcerer")
        self.assertEqual(snapshot.frame_id, 15)
        self.assertIn("render", snapshot.latencies_ms)
        self.assertIn("render", snapshot.p95_latencies_ms)
        self.assertGreater(snapshot.p95_latencies_ms["render"], snapshot.latencies_ms["render"])

    def test_multi_thread_safety(self):
        monitor = PerformanceMonitor(system_provider=NullSystemMetricsProvider())

        def _worker(thread_id: int):
            for _ in range(20):
                with monitor.profile(f"thread_{thread_id}"):
                    time.sleep(0.001)

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snapshot = monitor.get_snapshot()
        self.assertEqual(len(snapshot.latencies_ms), 4)

    def test_hud_toggle_state(self):
        monitor = PerformanceMonitor()
        self.assertFalse(monitor.display_enabled)

        # Toggle on
        self.assertTrue(monitor.toggle_display())
        self.assertTrue(monitor.display_enabled)

        # Toggle off
        self.assertFalse(monitor.toggle_display())
        self.assertFalse(monitor.display_enabled)

if __name__ == "__main__":
    unittest.main()
