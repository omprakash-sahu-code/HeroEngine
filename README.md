# HeroEngine - Creative Coding and Real-Time Interaction Framework

HeroEngine is a high-performance, real-time computer vision framework built in Python to render cinematic, superhero-inspired visual effects driven directly by hand tracking, body poses, and facial landmarks.

Natively powered by GPU acceleration using ModernGL, GLFW, and MediaPipe, the engine acts as an all-in-one pipeline, handling frame processing, gesture classification, shader execution, particle dynamics, and post-processing.

---

## 🚀 Getting Started

### 📋 Prerequisites
* Python 3.9 or higher
* A compatible webcam
* GPU support with OpenGL 3.3+ compatibility

### 🛠️ Installation
1. Clone the repository and navigate into the workspace.
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### 🎮 Running the Engine
Initialize and run the core bootstrapper:
```bash
python -m src.main
```

---

## 📂 Project Organization

```
HeroEngine/
├── docs/               # PRD, Architecture, Design, Contributing Guidelines
├── config/             # Global configurations (default.yaml)
├── assets/             # Global texture, sound, font assets
├── src/
│   ├── main.py         # Application Entry Point
│   ├── engine/
│   │   ├── core/       # Engine core loop & module manager
│   │   ├── vision/     # Isolated MediaPipe modules (hands, pose, face)
│   │   ├── gestures/   # Heuristic gesture parsing logic
│   │   ├── rendering/  # ModernGL renderer, camera, particle emitters
│   │   └── utils/      # Timers, Math, Geometry, Loggers
│   └── modules/        # Dynamic Hero Modules (e.g. sorcerer, iron, spider)
└── tests/              # Automated unit/integration tests
```

---

## 📚 Documentation
For deeper reading into the implementation specifics, review the directory [docs/](file:///f:/Project/HeroEngine/docs/):
* **[Product Requirements Document (PRD)](file:///f:/Project/HeroEngine/docs/PRD.md):** Target scopes, performance targets, and functional features.
* **[Architecture Specifications](file:///f:/Project/HeroEngine/docs/ARCHITECTURE.md):** Core class behaviors, flow systems, and runtime lifecycles.
* **[Technical Design Document](file:///f:/Project/HeroEngine/docs/DESIGN.md):** Mathematical models, coordinates maps, and circle-fitting heuristics.
* **[Effects Specifications Catalog](file:///f:/Project/HeroEngine/docs/EFFECT_SPEC.md):** Gesture activations, animation durations, and sound map references.
* **[Contributing Guidelines](file:///f:/Project/HeroEngine/docs/CONTRIBUTING.md):** Coding style parameters, PR rules, and standards for developers and AI agents.
