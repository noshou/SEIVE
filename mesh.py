import numpy as np
from beartype import beartype

@beartype
def mesh(
    thetaMax:  float|int,
    phiMax:    float|int,
    resolution: int
) -> tuple[np.ndarray, np.ndarray]:

    """
    Creates a mesh of theta and phi over interval

    Args:
        phiMax (_float_):     "latitude" ; polar/zenith 0 -> pi 
        thetaMax (_float_):   "longitude"; azimuth 0 -> 2pi
        resolution (_int_):   the grid resolution
        
    Returns:
        mesh: the mesh grid
    
    Raises:
        ValueError: if phi < 0 or phi > pi
        ValueError: if theta < 0 or theta > 2*pi
        ValueError: if resolution <= 0
    
    """
    
    if ((phiMax < 0.) or (phiMax > np.pi)):
        raise ValueError("phiMax is out of bounds")
    elif ((thetaMax < 0.) or (thetaMax >  2.* np.pi)):
        raise ValueError("thetaMax is out of bounds")
    elif ((resolution <= 0)):
        raise ValueError("resolution must be > 0")
    
    # grid parameters
    theta = np.linspace(0, thetaMax, resolution)
    phi   = np.linspace(0, phiMax,   resolution)
    
    # mesh
    thetaGrid, phiGrid = np.meshgrid(theta, phi)
    
    return thetaGrid, phiGrid
