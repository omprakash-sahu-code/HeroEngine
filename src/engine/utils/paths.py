import os
import sys

def resource_path(relative_path: str) -> str:
    """Get canonical absolute path to resource, working for source code and PyInstaller frozen bundles.

    Args:
        relative_path: Relative path string (e.g. 'config/default.yaml', 'src/modules', 'src/engine/rendering/shaders/hud.frag').

    Returns:
        str: Absolute system file path.
    """
    # Normalize path separators for cross-platform compatibility
    clean_path = relative_path.replace("/", os.sep).replace("\\", os.sep)
    if clean_path.startswith("." + os.sep):
        clean_path = clean_path[2:]

    # Isolated frozen detection (PyInstaller _MEIPASS handling)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = getattr(sys, '_MEIPASS')
    else:
        # Project root: src/engine/utils -> src/engine -> src -> project_root
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    return os.path.abspath(os.path.join(base_dir, clean_path))
