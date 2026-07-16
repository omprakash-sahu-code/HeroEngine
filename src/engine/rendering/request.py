from typing import Dict, Any

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
