# Product Requirement Document (PRD) - HeroEngine

## 1. Vision & Overview
HeroEngine is an open-source, real-time creative coding framework and computer vision application that translates real-world human gestures and poses into cinematic, superhero-inspired visual effects. 

The goal is to provide a premium, modular engine that owns the entire pipeline from frame capture to GPU-accelerated visual effects rendering. Rather than using proprietary or copyrighted assets, HeroEngine is a platform for demonstrating original visual designs driven by modern computer vision.

---

## 2. Target Audience & Use Cases
* **Creative Coders & Developers:** Looking for an extensible, high-performance base to prototype interactive visual effects.
* **Hobbyists & Tech Enthusiasts:** Users wanting to try "magic spellcasting" or superhero interactions via standard webcams.
* **Exhibition Designers:** Installation creators who can hook up the engine to projectors or stream coordinates via OSC to TouchDesigner/Unity/Unreal.

---

## 3. Core Capabilities & Core Modules
The initial launch focuses on the **Sorcerer Module** (inspired by mystical energy manipulation).

### 3.1 Gesture-to-Effect Features (Sorcerer)
* **Energy Shield (Mystic Aegis):** Summoned via an open-palm gesture facing the camera. The shield follows the hand, scales based on depth, and rotates continuously.
* **Mystic Portal:** Triggered when the user pinches index and thumb on both hands and pulls them apart. A ring of sparks expands and reveals a separate background scene inside the portal.
* **Eldritch Whips:** Activated via clenched-fist movements that drag glowing, physics-based lines through 3D space with particle trails.

---

## 4. Technical & Performance Requirements
To ensure a cinematic, high-fidelity experience, HeroEngine must satisfy the following constraints:

| Requirement | Target Metric | Metric Description |
| :--- | :--- | :--- |
| **Target Frame Rate** | 60 FPS (min 30 FPS) | The display window must update smoothly at these rates to avoid visual stuttering. |
| **End-to-End Latency** | < 50ms | Time from webcam exposure to the final pixel output on screen. |
| **Tracking Accuracy** | High confidence (>0.7) | Hand and pose landmarks must remain stable with minimal jitter. |
| **GPU Utilization** | Optimize shaders | Shaders must compile quickly (<500ms at startup) and execute efficiently. |

---

## 5. Functional Specifications

### 5.1 Capture & Processing Subsystem
* **Webcam Input:** Support configurable resolutions (default 720p at 30/60fps) and dynamic aspect ratio matching.
* **Vision Pipeline:** Integrate MediaPipe solutions asynchronously to prevent frame-drop in the main rendering thread.
* **Gesture Recognizer:** A rule-based spatial-temporal engine that reads geometric angles, distances, and trajectory histories to fire discrete events.

### 5.2 Rendering Subsystem
* **Graphics API:** Use ModernGL (OpenGL 3.3+ Core profile) to utilize vertex, fragment, and geometry shaders.
* **Post-Processing Pipeline:** Multi-pass rendering pipeline to support Bloom, HDR glow, and radial blur to make energy effects look bright and cinematic.
* **Particle System:** Compute-shader or instanced-rendering based particle engine capable of drawing 10,000+ active particles concurrently.

### 5.3 Modular Hero Framework
* **Dynamic Plugin Discovery:** The engine must inspect `src/modules/` at startup and automatically load classes inheriting from `HeroModule`.
* **Resource Loader:** Centralized loading of common textures, fonts, sounds, and global configurations.

---

## 6. Non-Functional Specifications
* **Code Quality & Extensibility:** All modules must conform to the strict API defined in `HeroModule`.
* **Platform Support:** Run natively on Windows 10/11, macOS, and Linux (requires Python 3.9+ and compatible OpenGL drivers).
* **Developer Guidelines:** Clear separation of concerns between raw computer vision (`src/engine/vision`), math/geometry (`src/engine/utils`), and visual effects (`src/engine/rendering`).
