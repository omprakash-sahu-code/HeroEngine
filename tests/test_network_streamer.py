import time
import unittest
from src.engine.network.models import TelemetryFrame
from src.engine.network.bus import TelemetryBus
from src.engine.network.osc_transport import OSCTransport
from src.engine.network.websocket_transport import WebSocketTransport
from src.engine.network.dispatcher import NetworkDispatcher

class MockTransport:
    def __init__(self):
        self.name = "Mock"
        self.is_active = True
        self.frames_received = []

    def start(self):
        self.is_active = True

    def send(self, frame: TelemetryFrame):
        self.frames_received.append(frame)

    def stop(self):
        self.is_active = False

class TestNetworkStreamer(unittest.TestCase):
    """Test suite covering TelemetryFrame, TelemetryBus, OSCTransport, WebSocketTransport, and NetworkDispatcher."""

    def test_telemetry_frame_dto_serialization(self):
        frame = TelemetryFrame(
            timestamp=123.456,
            frame_number=100,
            hands={"Right": {"centroid": (0.1, 0.2, 0.3), "pinch": 0.05}},
            gestures={"Right": "Open Palm"},
            module="iron",
            camera={"dx": 0.02, "dy": -0.01},
            fps=60.0
        )
        d = frame.to_dict()
        self.assertEqual(d["frame_number"], 100)
        self.assertEqual(d["module"], "iron")
        self.assertEqual(d["gestures"]["Right"], "Open Palm")

    def test_telemetry_bus_pub_sub(self):
        bus = TelemetryBus()
        received = []

        def callback(payload):
            received.append(payload)

        bus.subscribe("test_topic", callback)
        bus.publish("test_topic", "hello_world")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], "hello_world")

        bus.unsubscribe("test_topic", callback)
        bus.publish("test_topic", "ignored")
        self.assertEqual(len(received), 1)

    def test_osc_transport_packet_encoding(self):
        packet = OSCTransport.encode_osc("/heroengine/test", [1.5, 42, "hello"])
        self.assertTrue(len(packet) > 0)
        self.assertTrue(packet.startswith(b"/heroengine/test\x00"))

    def test_dispatcher_bounded_queue_non_blocking_eviction(self):
        dispatcher = NetworkDispatcher({"enabled": True})
        mock = MockTransport()
        dispatcher.add_transport(mock)
        dispatcher.start()

        # Push 50 frames rapidly
        for i in range(50):
            frame = TelemetryFrame(timestamp=time.perf_counter(), frame_number=i, module="iron")
            dispatcher.push_frame(frame)

        time.sleep(0.3)
        dispatcher.stop()

        # Verify dispatcher processed latest frames without crashing or blocking
        self.assertTrue(len(mock.frames_received) > 0)

    def test_dispatcher_delta_filtering(self):
        dispatcher = NetworkDispatcher({"enabled": True})
        mock = MockTransport()
        dispatcher.add_transport(mock)
        dispatcher.start()

        # Push 3 identical frames
        f1 = TelemetryFrame(timestamp=1.0, frame_number=1, module="iron", gestures={"Right": "Open Palm"})
        f2 = TelemetryFrame(timestamp=1.1, frame_number=2, module="iron", gestures={"Right": "Open Palm"})
        f3 = TelemetryFrame(timestamp=1.2, frame_number=3, module="iron", gestures={"Right": "Open Palm"})

        dispatcher.push_frame(f1)
        time.sleep(0.05)
        dispatcher.push_frame(f2)
        time.sleep(0.05)
        dispatcher.push_frame(f3)
        time.sleep(0.1)

        dispatcher.stop()

        # First frame should have module="iron", second frame module should be delta-filtered (None)
        if len(mock.frames_received) >= 2:
            self.assertEqual(mock.frames_received[0].module, "iron")
            self.assertIsNone(mock.frames_received[1].module)

    def test_transport_lifecycle_restart(self):
        osc = OSCTransport("127.0.0.1", 9005)
        osc.start()
        self.assertTrue(osc.is_active)
        osc.stop()
        self.assertFalse(osc.is_active)
        osc.start()
        self.assertTrue(osc.is_active)
        osc.stop()

if __name__ == "__main__":
    unittest.main()
