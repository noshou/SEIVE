import numpy as np
import plotly.graph_objects as go
from beartype import beartype

@beartype
def ellipticalSurface(
    a,b,c:   float|int, 
    thetaMax: float|int, 
    phiMax:   float|int
    ) -> go.Figure:
    """
    Plots a 3D parametric ellipsoid surface

    Args:
        a, b, c (_float_):    scaling along (x,y,z) axis respectivley
        phiMax (_float_):     "latitude" ; polar/zenith 0 -> pi 
        thetaMax (_float_):   "longitude"; azimuth 0 -> 2pi
        
    Returns:
        fig   the figure
    """
    
    # assertion checks
    if (a <= 0 or b <= 0 or c <= 0):
        raise ValueError("parameters are out of bound")
    elif ((phiMax < 0.) or (phiMax > np.pi)):
        raise ValueError("phiMax is out of bounds")
    elif ((thetaMax < 0.) or (thetaMax >  2.* np.pi)):
        raise ValueError("thetaMax is out of bounds")

    # parameters, grid
    theta = np.linspace(0, thetaMax, 100) # 
    phi   = np.linspace(0, phiMax,   100) # 

    # 2D grids for theta, phi
    thetaGrid, phiGrid = np.meshgrid(theta, phi)

    # parametric coordinates
    x = a * np.sin(phiGrid) * np.cos(thetaGrid)
    y = b * np.sin(phiGrid) * np.sin(thetaGrid)
    z = c * np.cos(phiGrid)

    # plotly figure
    fig = go.Figure(data=[go.Surface(x=x, y=y, z=z, colorscale='Brwnyl')])
    fig.update_layout(
        title='Interactive Parametric Sphere',
        scene=dict(
            aspectmode='data', # Keeps the sphere from looking stretched
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        )
    )
    
    return fig