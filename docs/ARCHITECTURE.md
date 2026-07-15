# Architecture Specification - HeroEngine

This document covers the high-level architecture of HeroEngine, defining its subsystem modules, data flow pipelines, and plugin API design.

---

## 1. System Block Diagram
HeroEngine divides work into isolated packages to maximize performance, clean interfaces, and support dynamic module loading.

```mermaid
graph TD
    A[Webcam Feed / Video File] -->|Raw Frame| B[Vision Pipeline]
    B -->|Normalized Landmarks| C[Engine Core / Module Manager]
    C -->|Dispatch to| E[Input Manager / Gesture Recognizer]
    E -->|Clean InputState/HandState| D[Active Hero Module]
    
    subgraph Engine Core Subsystems
        C
        E
        F[Global State Manager]
        C --> F
    end
    
    D -->|Render Commands| G[ModernGL Rendering Pipeline]
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

### 2.2 Input & Gesture Layer (`src/engine/gestures/` & `src/engine/core/input_manager.py`)
* **Input Manager:** Acts as a broker, receiving raw MediaPipe coordinates and packing them into an abstract `InputState` containing `HandState` structures. This decouples core modules from MediaPipe details.
* **Gesture Recognizer:** Evaluates geometric rules (angles, distances) to identify palm, pinch, and fist states, applying debouncers.

### 2.3 Rendering Subsystem (`src/engine/rendering/`)
* **Renderer (`renderer.py`):** Encapsulates the ModernGL context, binding shaders, textures, and targets.
* **Shaders & Objects:** Separate wrappers (`window.py`, `shader.py`, `texture.py`, `framebuffer.py`) for decoupled OpenGL operations.
* **Particle System:** Simple CPU particles (`particles.py`) that simulate sparks and glows.

### 2.4 Module Manager (`src/engine/core/engine.py`)
* Automatically discovers and instantiates modules in `src/modules/`.
* Dispatches abstract input states to `process_input()`, updates logic via `update()`, and commands rendering via `render()`.

---

## 3. Dynamic Module Plugin API (`HeroModule`)
Every hero module must implement the abstract base class `HeroModule` defined in `src/modules/base_module.py`.

```python
# Conceptual design of the Module Interface
from abc import ABC, abstractmethod
from typing import Any

class HeroModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the developer-friendly name of this module."""
        pass

    @abstractmethod
    def initialize(self, ctx) -> None:
        """Called once when the module is loaded. Sets up GL resources/shaders/assets."""
        pass

    @abstractmethod
    def process_input(self, input_state: Any) -> None:
        """Processes abstract input and gestures (e.g. HandState) and updates internal flags."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advances internal logic, particle simulations, and animation timelines."""
        pass

    @abstractmethod
    def render(self, renderer: Any) -> None:
        """Directs the renderer to draw specific module visual effects."""
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
  2. Process frame with MediaPipe (async) to update raw landmarks.
  3. Input Manager maps raw landmarks to abstract HandState / InputState.
  4. Active Hero Module processes inputs via process_input().
  5. Active Hero Module updates physics and animations via update().
  6. Clear screen buffer.
  7. Render camera background pass.
  8. Active Hero Module draws VFX overlays via render().
  9. Poll GLFW events & swap buffers.
  10. Loop back if window remains open.
```
