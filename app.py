import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, ALL
from mesh import mesh as create_mesh
from ellipticalSurface import ellipticalSurface
from sphericalHarmonicSurface import sphericalHarmonicSurface

app = Dash(__name__)
# =============================================================================
# LAYOUT — all control IDs always in DOM; visibility toggled via style
# =============================================================================
app.layout = html.Div([
    html.H1("Dynamic Parametric Surface Visualizer", style={'text-align': 'center'}),

    # Mode selector
    html.Div([
        html.Label("Surface Type:", style={'font-weight': 'bold'}),
        dcc.RadioItems(
            id='mode-selector',
            options=['Ellipsoid', 'Spherical Harmonics'],
            value='Ellipsoid',
            inline=True
        )
    ], style={'padding': '20px'}),

    # Ellipsoid controls (always in DOM)
    html.Div([
        html.Label("a (X-axis):"),
        dcc.Slider(id='a-slider', min=0.1, max=3, value=1, step=0.1),

        html.Label("b (Y-axis):"),
        dcc.Slider(id='b-slider', min=0.1, max=3, value=1, step=0.1),

        html.Label("c (Z-axis):"),
        dcc.Slider(id='c-slider', min=0.1, max=3, value=1, step=0.1),

        html.Label("Theta max (azimuth):"),
        dcc.Slider(id='theta-slider', min=0, max=2*np.pi, value=2*np.pi, step=0.1),

        html.Label("Phi max (polar):"),
        dcc.Slider(id='phi-slider', min=0, max=np.pi, value=np.pi, step=0.1),
    ], id='ellipsoid-controls', style={'padding': '20px', 'width': '400px'}),

    # Spherical Harmonics controls (always in DOM, hidden initially)
    html.Div([
        html.Label("L_max (max degree):"),
        dcc.Input(id='lmax-input', type='number', value=2, min=0, max=4, step=1),

        html.Label("r0 (base radius):"),
        dcc.Slider(id='r0-slider', min=0.5, max=2, value=1.0, step=0.1),

        html.Hr(),
        html.Label("Coefficients:", style={'font-weight': 'bold'}),
        html.Div(id='sh-sliders-container')
    ], id='sh-controls', style={'padding': '20px', 'width': '400px', 'display': 'none'}),

    # Graph
    dcc.Graph(id='sphere-graph')
], style={'max-width': '1000px', 'margin': '0 auto', 'font-family': 'sans-serif'})

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('ellipsoid-controls', 'style'),
    Output('sh-controls', 'style'),
    Input('mode-selector', 'value')
)
def toggle_controls(mode):
    shown  = {'padding': '20px', 'width': '400px'}
    hidden = {'padding': '20px', 'width': '400px', 'display': 'none'}
    if mode == 'Ellipsoid':
        return shown, hidden
    return hidden, shown


@app.callback(
    Output('sh-sliders-container', 'children'),
    Input('lmax-input', 'value')
)
def generate_sh_sliders(L_max):
    if L_max is None:
        return []

    L_max = int(L_max)
    pairs = [(l, m) for l in range(L_max + 1) for m in range(-l, l + 1)]

    return [
        html.Div([
            html.Label(f'Y_{l}^{{{m}}}:'),
            dcc.Slider(
                id={'type': 'sh-coeff', 'l': l, 'm': m},
                min=-0.3, max=0.3, value=0, step=0.01,
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ], style={'margin-bottom': '15px'})
        for l, m in pairs
    ]


@app.callback(
    Output('sphere-graph', 'figure'),
    Input('mode-selector', 'value'),
    Input('a-slider', 'value'),
    Input('b-slider', 'value'),
    Input('c-slider', 'value'),
    Input('theta-slider', 'value'),
    Input('phi-slider', 'value'),
    Input('lmax-input', 'value'),
    Input('r0-slider', 'value'),
    Input({'type': 'sh-coeff', 'l': ALL, 'm': ALL}, 'value'),
)
def update_graph(mode, a, b, c, theta_max, phi_max, L_max, r0, coeff_values):
    theta_val = theta_max if theta_max is not None else 2*np.pi
    phi_val   = phi_max   if phi_max   is not None else np.pi

    thetaGrid, phiGrid = create_mesh(theta_val, phi_val, resolution=100)

    if mode == 'Ellipsoid':
        x, y, z = ellipticalSurface(
            a or 1, b or 1, c or 1,
            thetaGrid, phiGrid
        )
        title = f'Ellipsoid: a={a:.1f}, b={b:.1f}, c={c:.1f}'

    else:
        r_val    = float(r0) if r0 is not None else 1.0
        lmax_int = int(L_max) if L_max is not None else None
        coeffs   = [float(v) if v is not None else 0.0 for v in coeff_values]
        expected = (lmax_int + 1) ** 2 if lmax_int is not None else 0

        if lmax_int is None or not coeffs or len(coeffs) != expected:
            x = r_val * np.sin(phiGrid) * np.cos(thetaGrid)
            y = r_val * np.sin(phiGrid) * np.sin(thetaGrid)
            z = r_val * np.cos(phiGrid)
            title = 'Spherical Harmonics (set L_max to add coefficients)'
        else:
            x, y, z = sphericalHarmonicSurface(lmax_int, coeffs, r_val, thetaGrid, phiGrid)
            non_zero = sum(1 for v in coeffs if abs(v) > 0.01)
            title = f'SH Surface: L_max={lmax_int}, r0={r_val:.1f}, {non_zero} active'

    fig = go.Figure(data=[go.Surface(
        x=x, y=y, z=z,
        colorscale='Brwnyl',
        showscale=False
    )])

    fig.update_layout(
        title=title,
        margin=dict(l=0, r=0, b=0, t=50),
        scene=dict(
            aspectmode='data',
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        ),
        height=700
    )

    return fig

# =============================================================================
# RUN
# =============================================================================
if __name__ == '__main__':
    app.run(debug=True)
