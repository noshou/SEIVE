import numpy as np
from beartype import beartype
from sphericalHarmonic import sphericalHarmonic as sh

@beartype
def orbitalSurface(
    l: int,
    m: int,
    thetaGrid: np.ndarray,
    phiGrid: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:

    """Computes the polar plot of a single spherical harmonic Y_l^m.

    Radial function: r(θ, φ) = |Y_l^m(θ, φ)|
    Surface color encodes the sign of Y_l^m (positive/negative lobes).

    Args:
        l:          Harmonic degree (≥ 0)
        m:          Harmonic order (-l ≤ m ≤ l)
        thetaGrid:  Azimuthal angles (0 → 2π)
        phiGrid:    Polar angles (0 → π)

    Returns:
        (x, y, z, Y): Cartesian coordinates + raw Y values for coloring
    """

    if l < 0:
        raise ValueError("l must be >= 0")
    if m < -l or m > l:
        raise ValueError("m must satisfy -l <= m <= l")
    if thetaGrid.shape != phiGrid.shape or thetaGrid.size == 0:
        raise ValueError("Invalid grid size")

    Y = sh(l, m, thetaGrid, phiGrid)
    r = np.abs(Y)

    x = r * np.sin(phiGrid) * np.cos(thetaGrid)
    y = r * np.sin(phiGrid) * np.sin(thetaGrid)
    z = r * np.cos(phiGrid)
    return x, y, z, Y
