# Technical Design Document - HeroEngine

This document describes the technical architecture, mathematical models, coordinate spaces, gesture recognition algorithms, and rendering workflows used in HeroEngine.

---

## 1. Coordinate Systems & Transformations
To render visuals accurately aligned with the user's hands and face, HeroEngine transforms coordinates across three distinct spaces:

```
[Webcam Pixel Space] ──────(Normalize)─────► [MediaPipe Coordinate Space]
(Width W, Height H)                           (x: 0..1, y: 0..1, z: normalized)
                                                         │
                                                  (Flip Y & Scale)
                                                         ▼
[OSC / Plugin Output] ◄────(Optional)─────── [OpenGL NDC Space]
(E.g., Unity/TouchDesigner)                  (x: -1..1, y: -1..1, z: scaled)
```

### 1.1 Camera Pixel Space
* Origin $(0, 0)$ is at the top-left of the camera frame.
* Range: $X \in [0, W]$, $Y \in [0, H]$.
* Hand landmarks returned by OpenCV operations are in this space.

### 1.2 MediaPipe Landmark Space
* Normalized coordinates: $x, y \in [0.0, 1.0]$.
* Origin $(0.0, 0.0)$ is at the top-left of the image.
* Depth $z$ represents landmark distance from the camera focal plane, scaled approximately to hand/body proportions.

### 1.3 OpenGL Normalized Device Coordinates (NDC)
* OpenGL coordinates require mapping to $[-1.0, 1.0]$ with the origin $(0, 0)$ at the center of the viewport.
* Flipped $Y$-axis (OpenGL's negative $Y$ is bottom; MediaPipe's positive $Y$ is bottom).
* Conversion formulae:
  $$X_{ndc} = (X_{mp} \times 2.0) - 1.0$$
  $$Y_{ndc} = 1.0 - (Y_{mp} \times 2.0)$$
  $$Z_{ndc} = Z_{mp} \times \text{depth\_scale}$$

---

## 2. Gesture Recognition Engine
The gesture recognizer uses heuristic geometric rules, angle estimations, and spatial-temporal history buffers.

### 2.1 Static Pose Detection
Static poses are evaluated per-frame based on landmark positions.

#### Open Palm Detection
An open palm is detected when all five fingers are extended away from the wrist. We verify that:
1. The distance between the wrist (Landmark 0) and the fingertips (Landmarks 4, 8, 12, 16, 20) is greater than the distance between the wrist and the respective Knuckle joints (MCP joints: Landmarks 2, 5, 9, 13, 17).
2. The fingers are not collapsed. This is measured by the joint angle:
   $$\theta = \arccos\left(\frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}\right)$$
   where $\mathbf{u}$ and $\mathbf{v}$ are vectors representing consecutive phalanges. We verify that $\theta \approx 180^\circ$ within a threshold of $\pm 25^\circ$.

#### Pinch Detection
A pinch gesture (between thumb tip $P_4$ and index tip $P_8$) is recognized if the Euclidean distance falls below a calibrated threshold $\epsilon_{pinch}$:
$$d(P_4, P_8) = \sqrt{(x_4 - x_8)^2 + (y_4 - y_8)^2 + (z_4 - z_8)^2} < \epsilon_{pinch}$$
Where $\epsilon_{pinch}$ is dynamically scaled based on the hand's bounding box size to remain depth-invariant.

### 2.2 Dynamic Gesture Recognition (Spatial-Temporal)
Dynamic gestures monitor coordinate changes over a sliding buffer of size $N$ frames (default $N = 30$ frames at 60 FPS, representing a 0.5-second history window).

#### Drawing Circular Patterns (Portal Summoning)
To detect if a user is tracing a circle:
1. We compute the centroid $(x_c, y_c)$ of the window coordinates.
2. We calculate the average radius:
   $$R = \frac{1}{N} \sum_{i=1}^{N} \sqrt{(x_i - x_c)^2 + (y_i - y_c)^2}$$
3. We compute the variance (residual error) of the points compared to the circle formula:
   $$\sigma^2 = \frac{1}{N} \sum_{i=1}^{N} \left( \sqrt{(x_i - x_c)^2 + (y_i - y_c)^2} - R \right)^2$$
4. A gesture is classified as circular if $\sigma^2$ is less than a tolerance threshold $\delta$ and the angular coverage of the sequence around the centroid approaches $2\pi$ radians ($360^\circ$).

---

## 3. State Management & Lifecycle
To prevent flickering or stuttering between gestures, the system implements a debouncing mechanism via state timers:

```
[Idle State] ──(Gesture Match > Debounce Frames)──► [Activating State]
      ▲                                                   │
      │                                            (Hold Duration)
      │                                                   ▼
[Cooldown State] ◄──────(Gesture Released)─────── [Active State]
```

* **Debounce Buffer:** A gesture must be consistently matched for $M$ consecutive frames (typically $M=3$) before triggering a state transition.
* **Cooldown Timers:** Prevents rapid re-triggering of high-intensity visual effects.

---

## 4. ModernGL Rendering Pipeline
Natively in Python, rendering runs over a GLFW context using ModernGL:
1. **Background Texture Pass:** A full-screen quad is rendered with the camera image loaded into a 2D OpenGL texture.
2. **Landmark overlay (Optional Debug):** Draws points and lines showing the underlying skeletal tracking mesh.
3. **VFX Overlay Pass:**
   * **Instanced Particles:** Vertex buffers storing particle positions, velocities, and lifespans. ModernGL updates these buffers, and an instanced draw call renders them as glowing billowed quads or circles.
   * **GLSL Fragment Effects:** Procedural textures (such as magic circles) are computed inside fragment shaders using distance fields and noise algorithms, avoiding heavy CPU image manipulations.
4. **Post-Processing Pass:** The frame is rendered to a Framebuffer Object (FBO). A second pass applies downscaled blur kernels to calculate bloom, which is blended back onto the final screen output.
