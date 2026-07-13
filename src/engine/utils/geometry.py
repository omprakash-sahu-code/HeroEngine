import numpy as np
from typing import Tuple, List, Optional

def fit_circle_2d(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
    """Fits a 2D circle to a set of points using algebraic circle fitting.

    Formula: (x - xc)^2 + (y - yc)^2 = R^2

    Args:
        points: List of (x, y) tuples.

    Returns:
        Optional[Tuple[float, float, float, float]]:
            (xc, yc, R, residual_variance) or None if calculation fails.
    """
    if len(points) < 5:
        return None
        
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    
    # Setup design matrix for algebraic circle fitting
    # A * a = b where a = [xc_scaled, yc_scaled, c_scaled]
    A = np.column_stack((x, y, np.ones_like(x)))
    b = x**2 + y**2
    
    try:
        # Solve least squares
        result, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        if len(result) < 3:
            return None
            
        xc = result[0] / 2.0
        yc = result[1] / 2.0
        r = np.sqrt(result[2] + xc**2 + yc**2)
        
        # Calculate residual variance
        distances = np.sqrt((x - xc)**2 + (y - yc)**2)
        variance = float(np.var(distances - r))
        
        return xc, yc, r, variance
    except (np.linalg.LinAlgError, ValueError):
        return None
