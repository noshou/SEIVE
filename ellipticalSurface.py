import numpy as np
from beartype import beartype

@beartype
def ellipticalSurface(
    a: float | int,
    b: float | int,
    c: float | int,
    thetaGrid: np.ndarray, 
    phiGrid:   np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    """
    Plots a 3D parametric ellipsoid surface

    Args:
        a, b, c:    scaling along (x,y,z) axis respectivley
        thetaGrid, phiGrid:   polar mesh grids
    Returns:
    [x,y,z] tuple of cartesian mesh grids
    """
    
    # assertion checks
    if (a <= 0 or b <= 0 or c <= 0):
        raise ValueError("parameters are out of bound")
    elif (thetaGrid.shape != phiGrid.shape or thetaGrid.size == 0):
        raise ValueError("Invalid grid size")

    # parametric coordinates
    x = a * np.sin(phiGrid) * np.cos(thetaGrid)
    y = b * np.sin(phiGrid) * np.sin(thetaGrid)
    z = c * np.cos(phiGrid)

    # return parameters
    
    return x,y,z