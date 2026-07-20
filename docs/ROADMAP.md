# HeroEngine Project Roadmap

This document outlines the multi-phase timeline and milestones for development, refinement, and expansion of the HeroEngine platform.

---

## Phase 1: Core Framework & Sorcerer MVP (Current Phase)
* **Goal:** Set up modular bootstrap rendering engine, vision pipeline, decoupled input layer, and initial sorcerer spells.
* **Milestones:**
  * **Phase 1.1 — Engine Bootstrap**
    * [x] Create GLFW windowing class (`window.py`) and ModernGL context wrappers.
    * [x] Create shader compiler, 2D texture, and custom framebuffer wrappers in `src/engine/rendering/`.
    * [x] Initialize global configs (`config/default.yaml`) and unified console logging.
  * **Phase 1.2 — Vision Pipeline**
    * [x] Integrate camera frame capturer and asynchronous MediaPipe Hands tracker.
    * [x] Build real-time performance logger/overlay (`monitor.py`).
  * **Phase 1.3 — Input & Gesture Layer**
    * [x] Create an `InputManager` translating tracking coordinates into unified `HandState` structures.
    * [x] Implement heuristic detection for static gestures (Open Palm, Pinch, Closed Fist) with debounce.
  * **Phase 1.4 — Doctor Strange MVP**
    * [x] Standardize the abstract `HeroModule` API.
    * [x] Build a lightweight CPU particle system to drive sparks and glow effects.
    * [x] Implement Doctor Strange spell visual effects (Mystic Orb -> Mystic Shield -> Eldritch Whip).


---

## Phase 2: Engine Consolidation & Post-Processing
* **Goal:** Polish rendering capabilities, add physics-based particle systems, and introduce advanced shaders.
* **Milestones:**
  1. [x] Implement multi-pass rendering framework inside `rendering/post_processing/` (Bloom, Blur, HDR overlay).
  2. [x] Build GPU-based particle emitter engine supporting instanced rendering.
  3. [x] Complete Sorcerer Module effects:
      * Eldritch Whips (dynamic physics trails).
      * Cinematic spell-charge effects (sparks pulling into the palms).
  4. [x] Standardize particle visual properties into a data-driven configuration & preset system.

---

## Phase 3: Framework Stabilization & Plugin System
* **Goal:** Standardize the `HeroModule` API to enable clean plug-and-play expansions and optimization.
* **Milestones:**
  1. [x] Refine the dynamic loader in `src/engine/core/engine.py` to auto-detect modules inside `src/modules/` dynamically.
  2. [x] Abstract and clean up the `vision/` wrappers to run in independent threads/processes via multiprocessing, preventing UI frame lag.
  3. [x] Standardize sound effect playback engine (using frame-requests & abstract backend).
  4. [x] Build a lightweight profiling utility (`src/engine/core/monitor.py`) displaying FPS, tracking latency, GPU compile times, and system load overlays.
  5. [x] Write unit tests for math utilities, gesture recognizers, and module loading lifecycle.

---

## Phase 4: Expansion Modules (Future Roadmap)
With a stabilized framework, we will develop subsequent modules mimicking other powers:

### 1. []Iron Module (Energy & UI HUD)
* **Visuals:** Repulsor beam rendering (GLSL circular charging and particle beam blast), high-tech glassmorphism HUD tracking head movements.
* **Gestures:** Wrist flexed upwards (facing palms forward) to fire repulsors.

### 2. []Spider Module (Web-slinging & Physics)
* **Visuals:** Web lines attached to physical screen coordinates, real-time rope physics using Verlet integration.
* **Gestures:** Double finger shoot (spider gesture) to deploy webs.

### 3. []Thunder Module (Electricity & Storm)
* **Visuals:** Branching lightning bolt shaders, screenshake, glowing lightning eyes (pose mesh tracking).
* **Gestures:** Raised hands clenched in fists to summon lightning from above.

### 4. []Chaos Module (Telekinetic Manipulation)
* **Visuals:** Red energy wisps swirling around fingers, object warping, telekinetic force fields.
* **Gestures:** Curved fingers facing down, moving hands dynamically to grab/push pixels.

---

## Phase 5: Production & Distribution
* **Goal:** Distribute HeroEngine as a compiled app or packaged python library.
* **Milestones:**
  1. [ ] Create a standalone binary packaging system (e.g. PyInstaller configuration).
  2. [ ] Establish OSC & WebSockets plugin documentation for seamless TouchDesigner and Unity external integrations.
  3. [ ] Release performance guidelines and benchmark reports on different GPU types.
