import cv2
import numpy as np
import threading
import time
import math
from typing import Dict, Any, Tuple, Optional
from src.engine.utils.logger import setup_logger

logger = setup_logger("Camera")

class CameraCapture:
    """Manages thread-safe asynchronous video capture from webcam or files

    without blocking the GUI main thread.
    """

    def __init__(self, config: Dict[str, Any]):
        """Args:

            config: Dictionary containing camera configurations.
        """
        self.config = config
        self.device_id = config.get("device_id", 0)
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)
        self.fps = config.get("fps", 30)
        
        self.cap = None
        self.frame = None
        self.running = False
        self.fallback_mode = False
        self.lock = threading.Lock()
        self.thread = None

    def start(self) -> bool:
        """Starts the background thread which initializes the camera context."""
        self.running = True
        self.thread = threading.Thread(target=self._capture_run, daemon=True)
        self.thread.start()
        # Return True instantly since the thread takes care of setup asynchronously
        return True

    def _capture_run(self) -> None:
        """Asynchronously initialize video device and run the capture loop."""
        logger.info(f"Asynchronously opening camera device: {self.device_id}")
        
        # Try DirectShow on Windows first for fast startup
        self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_DSHOW)
        
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            logger.info(f"Hardware camera opened. Active Resolution: {self.width}x{self.height}")
        else:
            logger.warning(f"Could not open hardware camera {self.device_id}. Initializing animated Mock Camera fallback mode.")
            self.fallback_mode = True
            if self.cap:
                self.cap.release()
                self.cap = None

        frame_counter = 0
        sleep_time = 1.0 / self.fps

        while self.running:
            start_time = time.perf_counter()
            
            if not self.fallback_mode:
                ret, frame = self.cap.read()
                if not ret:
                    # Camera disconnected or empty frame read
                    time.sleep(0.01)
                    continue
            else:
                # Generate a mock animated BGR frame (grid with bouncing target)
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                
                # Draw dynamic grid lines
                for i in range(0, self.width, 80):
                    cv2.line(frame, (i, 0), (i, self.height), (30, 30, 30), 1)
                for j in range(0, self.height, 80):
                    cv2.line(frame, (0, j), (self.width, j), (30, 30, 30), 1)
                
                # Draw text overlay
                cv2.putText(
                    frame, "MOCK CAMERA FEED", (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 255), 3
                )
                cv2.putText(
                    frame, "Move your hand inside view to test", (50, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2
                )
                
                # Draw bouncing target (representing simulated hand trace)
                x = int((self.width / 2) + 250 * math.sin(frame_counter * 0.05))
                y = int((self.height / 2) + 180 * math.cos(frame_counter * 0.05))
                cv2.circle(frame, (x, y), 20, (0, 0, 255), -1)
                cv2.circle(frame, (x, y), 10, (255, 255, 255), -1)
                
                frame_counter += 1

            # Update thread-safe frame pointer
            with self.lock:
                self.frame = frame
            
            # Maintain targeted FPS rate
            elapsed = time.perf_counter() - start_time
            delay = max(0.001, sleep_time - elapsed)
            time.sleep(delay)

        if self.cap:
            self.cap.release()
            self.cap = None

    def read_frame(self) -> Optional[cv2.Mat]:
        """Read the latest captured frame.

        Returns:
            Optional[cv2.Mat]: The BGR image frame or None if not ready.
        """
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self) -> None:
        """Stop background capture and release resources."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("Camera capture stopped cleanly.")
