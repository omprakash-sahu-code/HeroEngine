from dataclasses import dataclass
from typing import Dict, Optional

class ProfileSection:
    """Standardized profiling section identifiers."""
    VISION_FETCH = "vision_fetch"
    INPUT_UPDATE = "input_update"
    MODULE_UPDATE = "module_update"
    TEXTURE_UPLOAD = "texture_upload"
    POST_PROCESS = "post_process"
    RENDER_SWAP = "render_swap"
    AUDIO_PROCESS = "audio_process"

@dataclass(frozen=True)
class ProfileSnapshot:
    """Immutable snapshot capturing performance metrics at a specific frame tick."""
    frame_id: int
    fps: float
    frame_time_ms: float
    latencies_ms: Dict[str, float]
    p95_latencies_ms: Dict[str, float]
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    active_module_name: str = "none"
    vision_fps: Optional[float] = None
    vision_latency_ms: Optional[float] = None
