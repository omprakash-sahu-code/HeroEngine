import math
from typing import Tuple, List

def euclidean_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    """Calculate the 3D Euclidean distance between two points.

    Args:
        p1: Coordinates (x, y, z) of point 1.
        p2: Coordinates (x, y, z) of point 2.

    Returns:
        float: Calculated distance.
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

def calculate_angle_3d(p1: Tuple[float, float, float], 
                       p2: Tuple[float, float, float], 
                       p3: Tuple[float, float, float]) -> float:
    """Calculate the angle (in degrees) formed by three points, with p2 as the vertex.

    Args:
        p1: Point 1 coordinates.
        p2: Vertex point coordinates.
        p3: Point 3 coordinates.

    Returns:
        float: Angle in degrees in range [0, 180].
    """
    # Vectors
    v1 = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
    v2 = (p3[0] - p2[0], p3[1] - p2[1], p3[2] - p2[2])
    
    dot_product = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
    
    if mag1 * mag2 == 0:
        return 0.0
        
    cos_angle = dot_product / (mag1 * mag2)
    # Clamp to avoid domain errors in acos
    cos_angle = max(-1.0, min(1.0, cos_angle))
    
    return math.degrees(math.acos(cos_angle))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t.

    Args:
        a: Start value.
        b: End value.
        t: Interpolation factor (normally 0.0 to 1.0).

    Returns:
        float: Interpolated value.
    """
    return a + (b - a) * max(0.0, min(1.0, t))
