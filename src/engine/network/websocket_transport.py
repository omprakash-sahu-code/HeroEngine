import json
import socket
import threading
from typing import Set
from src.engine.network.transport import Transport
from src.engine.network.models import TelemetryFrame
from src.engine.utils.logger import setup_logger

logger = setup_logger("WebSocketTransport")

class WebSocketTransport(Transport):
    """WebSocket TCP telemetry broadcast transport."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self._host = host
        self._port = port
        self._server_socket: socket.socket = None
        self._clients: Set[socket.socket] = set()
        self._lock = threading.Lock()
        self._active = False
        self._thread: threading.Thread = None

    @property
    def name(self) -> str:
        return "WebSocket"

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Start TCP listener thread for WebSocket clients."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self._host, self._port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(0.5)
            self._active = True

            self._thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._thread.start()
            logger.info(f"WebSocketTransport streaming TCP packets to {self._host}:{self._port}")
        except Exception as e:
            logger.error(f"Failed starting WebSocketTransport: {e}")
            self._active = False

    def _accept_loop(self) -> None:
        """Background thread accepting client TCP connections."""
        while self._active:
            try:
                client_sock, _ = self._server_socket.accept()
                client_sock.setblocking(False)
                with self._lock:
                    self._clients.add(client_sock)
            except socket.timeout:
                continue
            except Exception:
                break

    def send(self, frame: TelemetryFrame) -> None:
        """Serialize TelemetryFrame to JSON and broadcast to connected TCP clients."""
        if not self._active:
            return

        with self._lock:
            if not self._clients:
                return

            payload_json = json.dumps(frame.to_dict())
            payload_bytes = (payload_json + "\n").encode('utf-8')
            dead_clients = set()

            for client in self._clients:
                try:
                    client.sendall(payload_bytes)
                except (BlockingIOError, OSError):
                    dead_clients.add(client)

            for dead in dead_clients:
                self._clients.remove(dead)
                try:
                    dead.close()
                except Exception:
                    pass

    def stop(self) -> None:
        """Shut down TCP server and close client connections."""
        self._active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        with self._lock:
            for client in self._clients:
                try:
                    client.close()
                except Exception:
                    pass
            self._clients.clear()

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        logger.info("WebSocketTransport stopped cleanly.")
