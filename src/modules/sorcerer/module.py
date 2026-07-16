import numpy as np
from typing import Dict, Any, List
from src.modules.base_module import HeroModule
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest
from src.engine.rendering.particles.particles import ParticleEmitter
from src.engine.utils.logger import setup_logger

logger = setup_logger("SorcererModule")

class SorcererModule(HeroModule):
    """Doctor Strange spell overlay module.

    Manages state machines, rotation timelines, and CPU particle systems,
    emitting abstract draw requests to the core renderer.
    """

    def name(self) -> str:
        return "sorcerer"

    def initialize(self) -> None:
        logger.info("Initializing Sorcerer (Doctor Strange) module...")
        
        # Continuous rotation values for shields and seals
        self.shield_rotation = 0.0
        
        # A particle emitter for whip sparks/trails
        self.emitter = ParticleEmitter(limit=5000)
        
        # Hand tracking states cached for update loop
        self.hands_state: Dict[str, HandState] = {}
        self.is_active = True

    def process_input(self, active_hands: Dict[str, HandState]) -> None:
        """Cache the latest parsed and debounced HandStates from the InputManager."""
        self.hands_state = active_hands

    def update(self, dt: float) -> None:
        if not self.is_active:
            return

        # 1. Advance rotation angles
        self.shield_rotation += 1.8 * dt  # Speed of rotation in radians/sec
        if self.shield_rotation > 2.0 * np.pi:
            self.shield_rotation -= 2.0 * np.pi

        # 2. Process hand states to spawn whip particles
        for label, hand in self.hands_state.items():
            if hand.gesture == "Closed Fist":
                # Spawn whip spark particles at the hand's centroid NDC
                x_ndc, y_ndc, _ = hand.get_centroid_ndc()
                
                # Check magnitude of hand velocity
                vx, vy, vz = hand.velocity
                vel_magnitude = np.sqrt(vx**2 + vy**2)
                
                # If moving fast, spawn more sparks and spread them along the movement path
                spawn_count = int(max(4, min(30, vel_magnitude * 15.0)))
                
                # Hot orange-red magic whip sparks
                color = (1.0, 0.45, 0.08)
                self.emitter.emit(x_ndc, y_ndc, count=spawn_count, color=color, speed=0.8)
                
            elif hand.gesture == "Open Palm":
                # Soft ambient sparks floating from the edges of the shield
                x_ndc, y_ndc, _ = hand.get_centroid_ndc()
                if np.random.rand() < 0.3: # 30% chance per frame
                    self.emitter.emit(x_ndc, y_ndc, count=1, color=(1.0, 0.6, 0.1), speed=0.2)

        # 3. Simulate existing active particles
        self.emitter.update(dt)

    def get_render_requests(self) -> List[EffectRequest]:
        """Generate the draw requests frame based on hand gestures."""
        requests: List[EffectRequest] = []

        if not self.is_active:
            return requests

        # 1. Add static spell effects mapping to hand gestures
        for label, hand in self.hands_state.items():
            centroid_ndc = hand.get_centroid_ndc()
            pos_2d = (centroid_ndc[0], centroid_ndc[1])
            
            if hand.gesture == "Open Palm":
                # Summon Mystic Aegis Shield
                requests.append(
                    EffectRequest(
                        "shield",
                        center=pos_2d,
                        radius=0.45,
                        rotation=self.shield_rotation,
                        color=(1.0, 0.42, 0.05) # Magic orange
                    )
                )
            elif hand.gesture == "Pinch":
                # Summon glowing Mystic Orb
                # Scale radius slightly depending on pinch distance
                radius = 0.15 + (hand.pinch_distance * 0.08)
                requests.append(
                    EffectRequest(
                        "orb",
                        center=pos_2d,
                        radius=radius,
                        color=(1.0, 0.5, 0.08)
                    )
                )

        # 2. Append whip/spark particles draw command (if active)
        points_data, count = self.emitter.get_render_data()
        if count > 0:
            requests.append(
                EffectRequest(
                    "particles",
                    points_data=points_data,
                    count=count,
                    base_size=16.0
                )
            )

        return requests

    def release(self) -> None:
        logger.info("Releasing Sorcerer Module state...")
        self.emitter.clear()
        self.hands_state.clear()
        self.is_active = False
