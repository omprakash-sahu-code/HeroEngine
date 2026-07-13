# HeroEngine Project Roadmap

This document outlines the multi-phase timeline and milestones for development, refinement, and expansion of the HeroEngine platform.

---

## Phase 1: Core Framework & Sorcerer MVP (Current Phase)
* **Goal:** Set up base architecture, vision pipeline, rendering engine, and the initial `sorcerer` module.
* **Milestones:**
  1. [x] Architectural Specification & Directory Structure definition.
  2. [ ] OpenCV + ModernGL + GLFW rendering pipeline initialization.
  3. [ ] Async MediaPipe Hands integration (`src/engine/vision/hands/`).
  4. [ ] Gesture recognition engine for static poses (e.g. open palm, pinch).
  5. [ ] Initial shader effects for the Sorcerer Module (Mystic Shield, Mystic Portal).
  6. [ ] Centralized settings manager (`config/default.yaml`).

---

## Phase 2: Engine Consolidation & Post-Processing
* **Goal:** Polish rendering capabilities, add physics-based particle systems, and introduce advanced shaders.
* **Milestones:**
  1. [ ] Implement multi-pass rendering framework inside `rendering/post_processing/` (Bloom, Blur, HDR overlay).
  2. [ ] Build GPU-based particle emitter engine supporting instanced rendering.
  3. [ ] Complete Sorcerer Module effects:
      * Eldritch Whips (dynamic physics trails).
      * Cinematic spell-charge effects (sparks pulling into the palms).
  4. [ ] Standardize sound effect playback engine triggered by state changes.

---

## Phase 3: Framework Stabilization & Plugin System
* **Goal:** Standardize the `HeroModule` API to enable clean plug-and-play expansions and optimization.
* **Milestones:**
  1. [ ] Refine the dynamic loader in `src/engine/core/engine.py` to auto-detect modules inside `src/modules/` dynamically.
  2. [ ] Abstract and clean up the `vision/` wrappers to run in independent threads/processes via multiprocessing, preventing UI frame lag.
  3. [ ] Build a lightweight profiling utility (`src/engine/core/monitor.py`) displaying FPS, tracking latency, GPU compile times, and system load overlays.
  4. [ ] Write unit tests for math utilities, gesture recognizers, and module loading lifecycle.

---

## Phase 4: Expansion Modules (Future Roadmap)
With a stabilized framework, we will develop subsequent modules mimicking other powers:

### 1. Iron Module (Energy & UI HUD)
* **Visuals:** Repulsor beam rendering (GLSL circular charging and particle beam blast), high-tech glassmorphism HUD tracking head movements.
* **Gestures:** Wrist flexed upwards (facing palms forward) to fire repulsors.

### 2. Spider Module (Web-slinging & Physics)
* **Visuals:** Web lines attached to physical screen coordinates, real-time rope physics using Verlet integration.
* **Gestures:** Double finger shoot (spider gesture) to deploy webs.

### 3. Thunder Module (Electricity & Storm)
* **Visuals:** Branching lightning bolt shaders, screenshake, glowing lightning eyes (pose mesh tracking).
* **Gestures:** Raised hands clenched in fists to summon lightning from above.

### 4. Chaos Module (Telekinetic Manipulation)
* **Visuals:** Red energy wisps swirling around fingers, object warping, telekinetic force fields.
* **Gestures:** Curved fingers facing down, moving hands dynamically to grab/push pixels.

---

## Phase 5: Production & Distribution
* **Goal:** Distribute HeroEngine as a compiled app or packaged python library.
* **Milestones:**
  1. [ ] Create a standalone binary packaging system (e.g. PyInstaller configuration).
  2. [ ] Establish OSC & WebSockets plugin documentation for seamless TouchDesigner and Unity external integrations.
  3. [ ] Release performance guidelines and benchmark reports on different GPU types.
