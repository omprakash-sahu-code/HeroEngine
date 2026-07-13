# Developer & AI Agent Contribution Guidelines

To ensure codebase consistency, high performance, and modularity, all developers and AI coding agents must adhere to the following standards when working on HeroEngine.

---

## 1. Code Style & Naming Conventions
We adhere to standard Python coding styles with minor enhancements for readability in creative coding environments:

* **General Style:** Follow [PEP 8](https://peps.python.org/pep-0008/) formatting. Keep lines below 100 characters.
* **Docstrings:** All classes, methods, and functions must have docstrings in Google format detailing arguments, return types, and exceptions.
* **Naming Conventions:**
  * **Classes:** UpperCamelCase (e.g., `SorcererModule`, `ParticleEmitter`).
  * **Functions & Methods:** snake_case (e.g., `update_particles()`, `check_pinch_distance()`).
  * **Variables & Arguments:** snake_case (e.g., `wrist_coordinate`, `delta_time`).
  * **Constants:** ALL_CAPS_SNAKE_CASE (e.g., `DEFAULT_CAMERA_ID`, `PINCH_THRESHOLD`).
  * **Shader Files:** snake_case with appropriate extensions (e.g., `shield_vertex.glsl`, `portal_fragment.frag`).

---

## 2. Directory & Folder Conventions
New features must be placed strictly in their designated directories:
* **Global Core Logic:** Write to `src/engine/core/`. Do not pollute this folder with hero-specific details.
* **New Vision Detectors:** Add folders inside `src/engine/vision/` (e.g., `src/engine/vision/segmentation/`).
* **Hero Modules:** All new characters or ability modules must live inside `src/modules/<hero_name>/`.
* **Global Assets:** Put shared assets in `assets/models/`, `assets/textures/`, `assets/sounds/`, or `assets/fonts/`. Module-specific assets can reside inside `src/modules/<hero_name>/assets/`.

---

## 3. Core Architecture Rules
* **Separation of Concerns:** Keep raw tracking (`vision/`) decoupled from graphics rendering (`rendering/`). Rendering elements should only read computed coordinates and gesture states.
* **No Direct Core Modifications from Modules:** Hero modules must not alter the core engine state directly. They must use the public API hooks defined in the `HeroModule` base class.
* **Performance Integrity:** Avoid blocking operations in the main thread (such as loading large texture files or initializing complex shaders mid-loop). Perform these operations in the initialization lifecycle hooks.

---

## 4. How Hero Modules Work (Developer Specification)
When implementing a new Hero Module, you must follow these steps:
1. Create a subfolder inside `src/modules/` named after the ability theme (e.g. `src/modules/thunder/`).
2. Inside that directory, create a `module.py` file containing a class that inherits from `HeroModule` (e.g., `class ThunderModule(HeroModule)`).
3. Ensure the module registers its configurations dynamically and cleans up all allocated OpenGL resources (textures, shaders, buffer objects) in the `release()` hook.

---

## 5. Pull Request (PR) Checklist
Before submitting code changes, complete the following checklist:
- [ ] Code follows Python PEP 8 formatting rules.
- [ ] No placeholder values or half-implemented methods are present.
- [ ] All allocated GPU buffers and OpenGL textures are correctly released/deleted during cleanup.
- [ ] Performance benchmarks are validated: no frame rates below 30 FPS.
- [ ] Unit tests are written for new gesture utilities or math functions.
- [ ] The `docs/EFFECT_SPEC.md` has been updated with any new spell definitions or modifications.
