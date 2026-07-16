import numpy as np
from typing import Dict, Any, List
from src.modules.base_module import HeroModule
from src.engine.core.input_manager import HandState
from src.engine.rendering.request import EffectRequest
from src.engine.physics.verlet_chain import VerletChain
from src.engine.utils.logger import setup_logger

logger = setup_logger("SorcererModule")

class SorcererModule(HeroModule):
    """Doctor Strange spell overlay module.

    Manages state machines, rotation timelines, and Verlet constraint physics chains,
    emitting abstract draw requests to the core renderer.
    """

    def name(self) -> str:
        return "sorcerer"

    def initialize(self) -> None:
        logger.info("Initializing Sorcerer (Doctor Strange) module...")
        
        # Continuous rotation values for shields and seals
        self.shield_rotation = 0.0
        
        # A dictionary mapping active hand labels to their corresponding VerletChain whips
        self.whips: Dict[str, VerletChain] = {}
        
        # A queue of particle emission requests to be consumed by the renderer
        self.pending_emissions = []
        
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

        # Remove whips for hands that are no longer active/present
        active_labels = set(self.hands_state.keys())
        self.whips = {label: whip for label, whip in self.whips.items() if label in active_labels}

        # 2. Process hand states to spawn whip particles and spell-charge effects
        for label, hand in self.hands_state.items():
            x_ndc, y_ndc, _ = hand.get_centroid_ndc()

            if hand.gesture == "Closed Fist":
                # Manage dynamic Verlet chain rope simulation
                if label not in self.whips:
                    self.whips[label] = VerletChain(
                        num_nodes=15,
                        link_distance=0.045,
                        gravity=(0.0, -0.45),
                        damping=0.93,
                        initial_anchor=(x_ndc, y_ndc)
                    )
                
                whip = self.whips[label]
                whip.update((x_ndc, y_ndc), dt)
                
                # Emit sparks all along the simulated nodes of the whip for a fluid trail
                for node_pos in whip.positions:
                    if np.random.rand() < 0.7:  # Organic density control
                        self.pending_emissions.append({
                            "center": (node_pos[0], node_pos[1]),
                            "count": 1,
                            "preset": "whip_trail"
                        })
                
            elif hand.gesture == "Pinch":
                # Remove active whips if transitioning to pinch
                if label in self.whips:
                    del self.whips[label]

                # Spell-Charge Vortex: Emit sparks spiraling inward to the palm using spell_charge preset
                # Spawn 3 spiral particles per frame per hand
                for _ in range(3):
                    self.pending_emissions.append({
                        "center": (x_ndc, y_ndc),
                        "count": 1,
                        "preset": "spell_charge"
                    })
                
            elif hand.gesture == "Open Palm":
                # Remove active whips if transitioning to open palm
                if label in self.whips:
                    del self.whips[label]

                # Soft ambient sparks floating from the edges of the shield
                if np.random.rand() < 0.3:
                    self.pending_emissions.append({
                        "center": (x_ndc, y_ndc),
                        "count": 1,
                        "preset": "shield_ambient"
                    })

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
                radius = 0.15 + (hand.pinch_distance * 0.08)
                requests.append(
                    EffectRequest(
                        "orb",
                        center=pos_2d,
                        radius=radius,
                        color=(1.0, 0.5, 0.08)
                    )
                )

        # 2. Append whip/spark particle emit commands using preset keys
        for emission in self.pending_emissions:
            requests.append(
                EffectRequest(
                    "emit_particles",
                    center=emission["center"],
                    count=emission["count"],
                    preset=emission["preset"]
                )
            )
        self.pending_emissions.clear()

        return requests

    def release(self) -> None:
        logger.info("Releasing Sorcerer Module state...")
        self.pending_emissions.clear()
        self.whips.clear()
        self.hands_state.clear()
        self.is_active = False
