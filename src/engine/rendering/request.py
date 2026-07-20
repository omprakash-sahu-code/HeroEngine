from typing import Dict, Any

class EffectType:
    """Standardized rendering effect identifiers."""
    ORB = "orb"
    SHIELD = "shield"
    PARTICLES = "particles"
    WHIP = "whip"
    REPULSOR_RING = "repulsor_ring"
    REPULSOR_BEAM = "repulsor_beam"
    REPULSOR_FLASH = "repulsor_flash"
    HUD_TARGET = "hud_target"
    POLYLINE = "polyline"
    WEB_PROJECTILE = "web_projectile"
    WEB_SPLATCH = "web_splatch"
    WEB_RETICLE = "web_reticle"

class EffectRequest:
    """A data structure representing a decoupled drawing command emitted by HeroModules.

    These requests are processed by the core Renderer to execute ModernGL draw calls
    without letting modules access GPU contexts directly.
    """

    def __init__(self, effect_type: str, **kwargs):
        """Args:

            effect_type: The type name of the effect (e.g. 'orb', 'shield', 'particles').
            **kwargs: Configuration values (positions, scales, rotations, colors, etc.).
        """
        self.effect_type = effect_type
        self.data: Dict[str, Any] = kwargs
