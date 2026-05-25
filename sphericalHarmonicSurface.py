import numpy as np
from beartype import beartype
from sphericalHarmonic import sphericalHarmonic as sh

@beartype
def sphericalHarmonicSurface(
    lMax: int,
    coeffs: list[float],
    r0: float,
    thetaGrid: np.ndarray,
    phiGrid: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    """Computes surface deformed by spherical harmonics up to degree lMax.
    
    Radial function: r(θ, φ) = r0 + Σ a_lm * Y_l^m(θ, φ)
    
    Args:
        lMax:       Maximum harmonic degree (includes all l ≤ lMax)
        
        coeffs:     Coefficients (a_lm) in summation order:
                    Σ_{l=0}^{lMax} Σ_{m=-l}^{l} a_lm Y_l^m ->
                    (0,0), (1,-1), (1,0), (1,1), (2,-2), ...
                    Length must be (lMax + 1)²
        r0:         Base sphere radius
        thetaGrid:  Azimuthal angles (0 → 2π)
        phiGrid:    Polar angles (0 → π)
    
    Returns:
        (x, y, z): Cartesian coordinates of surface
    """
    
    # assertion checks
    if (lMax < 0):
        raise ValueError("lMax must be >= 0")
    elif (len(coeffs) != (lMax + 1)**2):
        raise ValueError("size mismatch betwewen coeffs and lMax")
    elif (thetaGrid.shape != phiGrid.shape or thetaGrid.size == 0):
        raise ValueError("Invalid grid size")

    # initialize radius mesh
    r = np.full_like(thetaGrid, r0)
    
    # generate (l,m) pairs, calculate Y, update r
    rIdx = 0
    for l in range(lMax + 1):
        for m in range(-l, l + 1):
            Y = sh(l, m, thetaGrid, phiGrid)
            r += coeffs[rIdx] * Y
            rIdx += 1

    # convert to cartesian coordinates
    x = r * np.sin(phiGrid) * np.cos(thetaGrid)
    y = r * np.sin(phiGrid) * np.sin(thetaGrid)
    z = r * np.cos(phiGrid)
    return x,y,z
