# Architecture Specification - HeroEngine

This document covers the high-level architecture of HeroEngine, defining its subsystem modules, data flow pipelines, and plugin API design.

---

## 1. System Block Diagram
HeroEngine divides work into isolated packages to maximize performance, clean interfaces, and support dynamic module loading.

```mermaid
graph TD
    A[Webcam Feed / Video File] -->|Raw Frame| B[Vision Pipeline]
    B -->|Normalized Landmarks| C[Engine Core / Module Manager]
    C -->|Dispatch Coordinates| D[Active Hero Module]
    
    subgraph Engine Core Subsystems
        C
        E[Gesture Recognizer]
        F[Global State Manager]
        C --> E
        C --> F
    end
    
    D -->|Gesture State & Hand Locations| G[ModernGL Rendering Pipeline]
    G -->|GLFW Window Render| H[Display Output]
    G -->|Optional Plugin| I[OSC / WebSocket Output]
end
```

---

## 2. Core Subsystems

### 2.1 Vision Pipeline (`src/engine/vision/`)
* **Camera Capture (`src/engine/vision/camera.py`):** Handles camera hardware selection, sets capture resolution/FPS, and serves frames.
* **Tracking Abstractions:**
  * `hands/detector.py`: Evaluates and exposes hand landmarks.
  * `pose/detector.py`: Evaluates and exposes full-body poses.
  * `face/detector.py`: Evaluates facial meshes.

### 2.2 Gesture Recognition (`src/engine/gestures/`)
* Contains mathematical algorithms (defined in [DESIGN.md](file:///f:/Project/HeroEngine/docs/DESIGN.md)) to parse hand and body landmarks.
* Translates continuous coordinate data into discrete events (e.g. `GESTURE_PINCH_START`, `GESTURE_PALM_RELEASE`).

### 2.3 Rendering Subsystem (`src/engine/rendering/`)
* **Renderer (`renderer.py`):** Holds the GLFW window handle and manages the ModernGL OpenGL Context.
* **Effects Controller (`effects/`):** Controls custom shaders, vertex specifications, buffer mappings, and textures.
* **Particle System (`particles/`):** Manages particle life cycles, physics updates (gravity, noise fields), and instanced drawing logic.

### 2.4 Module Manager (`src/engine/core/engine.py`)
* Automatically discovers and instantiates hero plugins located in the `src/modules/` directory.
* Delegates input events to the currently active module and manages module swapping (e.g., swapping from `SorcererModule` to `IronModule`).

---

## 3. Dynamic Module Plugin API (`HeroModule`)
Every hero module must implement the abstract base class `HeroModule` defined in `src/modules/base_module.py`.

```python
# Conceptual design of the Module Interface
from abc import ABC, abstractmethod

class HeroModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the developer-friendly name of this module."""
        pass

    @abstractmethod
    def initialize(self, ctx) -> None:
        """Called once when the module is loaded. Sets up GL resources/shaders."""
        pass

    @abstractmethod
    def update(self, landmarks, delta_time: float) -> None:
        """Processes coordinates, calculates active states, and updates internal animation clocks."""
        pass

    @abstractmethod
    def render(self, ctx) -> None:
        """Renders specific module visual effects to the current framebuffer."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Cleans up textures, buffers, and shaders when the module is unloaded."""
        pass
```

---

## 4. Main Event Loop Lifecycle
The primary execution sequence within `src/main.py` runs on a single main thread for OpenGL compatibility, with the CV frame processing offloaded to sub-threads where possible:

```
[Start Engine] ──► [Initialize ModernGL & GLFW] ──► [Load Active Hero Module]
                                                            │
┌───────────────────────────────────────────────────────────┘
▼
[Frame Loop]:
  1. Capture webcam frame.
  2. Process frame with MediaPipe (async) to update landmarks.
  3. Run Gesture Recognition on new landmarks.
  4. Update Active Hero Module state (particles, trigger clocks).
  5. Clear screen buffer.
  6. Render camera background pass.
  7. Render Active Module visual effects overlay (ModernGL draw calls).
  8. Apply Post-processing pass (Bloom / Blur).
  9. Poll GLFW events & swap buffers.
  10. Loop back if window remains open.
```
