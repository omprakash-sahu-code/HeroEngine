import socket
import struct
from typing import Dict, Any, List
from src.engine.network.transport import Transport
from src.engine.network.models import TelemetryFrame
from src.engine.utils.logger import setup_logger

logger = setup_logger("OSCTransport")

class OSCTransport(Transport):
    """OSC (Open Sound Control) UDP network transport."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        self._host = host
        self._port = port
        self._socket: socket.socket = None
        self._active = False

    @property
    def name(self) -> str:
        return "OSC"

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Initialize non-blocking UDP socket."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setblocking(False)
            self._active = True
            logger.info(f"OSCTransport streaming UDP packets to {self._host}:{self._port}")
        except Exception as e:
            logger.error(f"Failed starting OSCTransport: {e}")
            self._active = False

    def send(self, frame: TelemetryFrame) -> None:
        """Serialize and send TelemetryFrame packets over OSC channels."""
        if not self._active or not self._socket:
            return

        try:
            # 1. Stream Hand Landmark Telemetry
            for label, hand in frame.hands.items():
                pos = hand.get("centroid", (0.0, 0.0, 0.0))
                gesture = frame.gestures.get(label, "None")
                self._send_osc_msg(
                    f"/heroengine/hand/{label.lower()}",
                    [float(pos[0]), float(pos[1]), float(pos[2]), str(gesture)]
                )

            # 2. Stream Active Module State
            if frame.module:
                self._send_osc_msg("/heroengine/module", [str(frame.module)])

            # 3. Stream Camera Impulse Offsets
            if frame.camera:
                self._send_osc_msg(
                    "/heroengine/camera/shake",
                    [float(frame.camera.get("dx", 0.0)), float(frame.camera.get("dy", 0.0))]
                )

            # 4. Stream Performance FPS Metric
            self._send_osc_msg("/heroengine/fps", [float(frame.fps)])

        except Exception as e:
            logger.debug(f"OSC send error: {e}")

    def _send_osc_msg(self, address: str, args: List[Any]) -> None:
        """Encode and dispatch a single OSC message packet over UDP socket."""
        packet = self.encode_osc(address, args)
        try:
            self._socket.sendto(packet, (self._host, self._port))
        except (BlockingIOError, OSError):
            pass  # Ignore non-blocking UDP send buffer full errors

    @staticmethod
    def encode_osc(address: str, args: List[Any]) -> bytes:
        """Build standard OSC byte packet."""
        # Align address string to 4-byte boundary
        addr_bytes = address.encode('utf-8') + b'\x00'
        addr_padded = addr_bytes + b'\x00' * ((4 - (len(addr_bytes) % 4)) % 4)

        types_str = ","
        data_payload = b""

        for arg in args:
            if isinstance(arg, float):
                types_str += "f"
                data_payload += struct.pack(">f", arg)
            elif isinstance(arg, int):
                types_str += "i"
                data_payload += struct.pack(">i", arg)
            else:
                types_str += "s"
                s_bytes = str(arg).encode('utf-8') + b'\x00'
                s_padded = s_bytes + b'\x00' * ((4 - (len(s_bytes) % 4)) % 4)
                data_payload += s_padded

        types_bytes = types_str.encode('utf-8') + b'\x00'
        types_padded = types_bytes + b'\x00' * ((4 - (len(types_bytes) % 4)) % 4)

        return addr_padded + types_padded + data_payload

    def stop(self) -> None:
        """Close UDP socket."""
        self._active = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        logger.info("OSCTransport stopped cleanly.")
