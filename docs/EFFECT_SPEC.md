# Visual Effects (VFX) Specification Catalog

This document specifies the trigger gestures, animation curves, timings, sound cues, cooldowns, and shader bindings for all Hero Module abilities.

---

## 1. Sorcerer Module Spells

### 1.1 Mystic Shield (Aegis of Light)
* **Trigger:** Open Palm gesture (facing webcam) with hand tracking confidence above 0.8.
* **Anchor Point:** Wrist landmark (Landmark 0) or Palm Center (geometric mean of Landmarks 0, 5, 9, 13, 17).
* **Cooldown:** 0.0 seconds (can be toggled instantly).
* **State Behavior:** Continuous tracking.
* **Timings & Animation:**
  * **0ms → 250ms (Summon):** The circular shield scales from $0.0$ to $1.2$ times the hand bounding-box size. Glow intensity ramps up linearly.
  * **Active Loop:** Continuously rotates at a rate of $\omega = 0.5$ radians/sec. Sub-rings rotate in counter directions.
  * **Dismissal (250ms → 0ms):** When hand is closed or tracking is lost, shield scales down to $0.0$ and fades.
* **Audio Track:** `assets/sounds/sorcerer/shield_summon.wav` (low-frequency dynamic drone).
* **Shader References:**
  * **Vertex Shader:** `src/modules/sorcerer/assets/shaders/shield_vertex.glsl`
  * **Fragment Shader:** `src/modules/sorcerer/assets/shaders/shield_fragment.glsl`

---

### 1.2 Mystic Portal (Planetary Gateway)
* **Trigger:** Both hands start in close contact (index tips touching), pinch gesture activated on both hands, then drawn apart horizontally.
* **Anchor Point:** Center coordinate between the two hands.
* **Cooldown:** 3.0 seconds after dismissal.
* **State Behavior:** Stays locked in global 3D space once created, independent of hand movement, until closed.
* **Timings & Animation:**
  * **0ms → 800ms (Expansion):** A circular ring of high-velocity spark particles expands from $0.0$ radius to target radius (calculated from the distance drawn between hands, max 1.5 meters in world coordinates).
  * **Active Loop:** Ring edges emit sparks flying outwards using random noise fields. The interior of the circle renders a separate scene using a parallax projection.
  * **Dismissal:** Triggered by an open palm passing through the portal or pinching hands back together. Portal collapses into a single dot and vanishes over $300\text{ ms}$.
* **Audio Track:** `assets/sounds/sorcerer/portal_open.wav` (sparkly crackling followed by a hum).
* **Shader References:**
  * **Vertex Shader:** `src/modules/sorcerer/assets/shaders/portal_vertex.glsl`
  * **Fragment Shader:** `src/modules/sorcerer/assets/shaders/portal_fragment.glsl`

---

### 1.3 Eldritch Whips (Mystic Lash)
* **Trigger:** Closed fist gesture (with rapid acceleration motion, detected via coordinate history).
* **Anchor Point:** Index finger knuckle base (Landmark 5) of the fist.
* **Cooldown:** 0.0 seconds.
* **State Behavior:** Active while the fist remains clenched.
* **Timings & Animation:**
  * **0ms → 150ms:** A glowing spark appears at the knuckle.
  * **Action Loop:** As the hand moves, a spline curve (using Bézier curves) is calculated connecting the current hand position to the historical track points. Sparks and smoke particles are spawned along the curve, fading out over a $600\text{ ms}$ lifespan.
  * **Dismissal:** Instantly vanishes when the fist is opened.
* **Audio Track:** `assets/sounds/sorcerer/whip_crack.wav` (acoustic crack sound on high-velocity whip snap).
* **Shader References:**
  * **Vertex Shader:** `src/modules/sorcerer/assets/shaders/whip_vertex.glsl`
  * **Fragment Shader:** `src/modules/sorcerer/assets/shaders/whip_fragment.glsl`
