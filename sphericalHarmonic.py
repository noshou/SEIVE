import numpy as np
from beartype import beartype
from scipy.special import lpmv
from scipy.special import factorial as fact

@beartype
def sphericalHarmonic(
    l: int,
    m: int, 
    thetaGrid: np.ndarray, 
    phiGrid:   np.ndarray
    ) -> np.ndarray:
    
    """Compute spherical harmonic Y_l^m on a grid.

    Args:
        l: Degree (0, 1, 2, ...). Controls overall shape complexity.
        m: Order (-l ≤ m ≤ l). Controls angular structure.
        thetaGrid: Azimuthal angle grid (0 → 2π)
        phiGrid: Polar angle grid (0 → π)
    Returns:
        Y: Y_l^m values at each (theta, phi) grid point
    """
    
    # assertion checks
    if (l < 0):
        raise ValueError("l is out of bound")
    elif ((m < -l) or (m > l)):
        raise ValueError("m is out of bounds")
    elif (thetaGrid.shape != phiGrid.shape or thetaGrid.size == 0):
        raise ValueError("Invalid grid size")
    
    # calculate associated legendre polynomial
    P = lpmv(abs(m), l, np.cos(phiGrid))
    
    # calculate azimuthal 
    if m == 0:
        azimuthal = 1.0
    elif m > 0:
        azimuthal = np.sqrt(2) * np.cos(m * thetaGrid)
    else:  
        azimuthal = np.sqrt(2) * np.sin(abs(m) * thetaGrid)    
    
    # calculate normilization constant
    N = np.sqrt((2*l+1)/(4*np.pi) * (fact(l-abs(m),True)/(fact(l+abs(m),True))))
    
    # calculate radial function
    Y = N * P * azimuthal
    
    return Y