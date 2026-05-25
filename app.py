import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ALL
from mesh import mesh as create_mesh
from ellipticalSurface import ellipticalSurface
from sphericalHarmonicSurface import sphericalHarmonicSurface
from orbitalSurface import orbitalSurface

app = Dash(__name__)

_dim = {'color': '#888', 'font-size': '0.85em', 'margin': '4px 0 12px 0'}

# Store for SH coefficients  avoids mixing pattern-matched ALL inputs with
# list-valued checklist inputs in the same callback (Dash 4 dispatcher bug)
_sh_coeff_store = dcc.Store(id='sh-coeffs-store', data=[])

LEFT_W  = 480
GRAPH_W = f'calc(100% - {LEFT_W + 20}px)'

# =============================================================================
# LAYOUT
# =============================================================================
app.layout = html.Div([
    _sh_coeff_store,
    html.H1("Dynamic Parametric Surface Visualizer", style={'text-align': 'center'}),

    # ── shared header controls ───────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Label("Surface Type:", style={'font-weight': 'bold'}),
            dcc.RadioItems(
                id='mode-selector',
                options=['Ellipsoid', 'Spherical Harmonics', 'Orbital'],
                value='Ellipsoid',
                inline=True
            )
        ], style={'margin-bottom': '12px'}),

        html.Div([
            html.Label("θ max (azimuth):"),
            dcc.Slider(id='theta-slider', min=0, max=2*np.pi,
                       value=2*np.pi, step=0.1),
        ], style={'margin-bottom': '4px'}),

        html.Div([
            html.Label("φ max (polar):"),
            dcc.Slider(id='phi-slider', min=0, max=np.pi,
                       value=np.pi, step=0.1),
        ]),
    ], style={'padding': '20px', 'border-bottom': '1px solid #ddd'}),

    # ── main body: controls left, graph right ───────────────────────────────
    html.Div([

        # Left column
        html.Div([

            # Ellipsoid panel
            html.Div([
                html.H3("Ellipsoid", style={'margin-top': 0}),
                html.P("Base shape  axes scale the sphere along X, Y, Z.",
                       style=_dim),

                html.Label("a (X-axis):"),
                dcc.Slider(id='a-slider', min=0.1, max=3, value=1, step=0.1),

                html.Label("b (Y-axis):"),
                dcc.Slider(id='b-slider', min=0.1, max=3, value=1, step=0.1),

                html.Label("c (Z-axis):"),
                dcc.Slider(id='c-slider', min=0.1, max=3, value=1, step=0.1),
            ], id='ellipsoid-controls', style={'padding': '16px'}),

            # Spherical Harmonics panel
            html.Div([
                html.H3("Spherical Harmonics", style={'margin-top': 0}),
                html.P("Deforms the base sphere (r₀) by adding harmonic terms Σ aₗₘ Yₗᵐ.",
                       style=_dim),

                html.Label("L_max (max degree):"),
                dcc.Input(id='lmax-input', type='number', value=2, min=0, step=1,
                          style={'width': '60px', 'margin-bottom': '12px'}),

                html.Label("r₀ (base radius):"),
                dcc.Slider(id='r0-slider', min=0.5, max=2, value=1.0, step=0.1),

                html.Hr(),
                html.Label("Coefficients aₗₘ:", style={'font-weight': 'bold'}),
                html.Div(id='sh-sliders-container')
            ], id='sh-controls', style={'padding': '16px', 'display': 'none'}),

            # Orbital panel
            html.Div([
                html.H3("Orbital", style={'margin-top': 0}),
                html.P("Polar plot of |Yₗᵐ|  radius encodes magnitude, color encodes sign.",
                       style=_dim),

                html.Label("l (degree):"),
                html.Div(
                    dcc.Slider(
                        id='orbital-l-selector',
                        min=0, max=6, value=1, step=1,
                        marks={i: str(i) for i in range(7)},
                    ),
                    style={'margin-bottom': '20px'}
                ),

                html.Label("m (order):", style={'display': 'block', 'margin-bottom': '6px'}),
                dcc.Checklist(
                    id='orbital-m-checklist',
                    options=[{'label': ' 0', 'value': 0}],
                    value=[0],
                    inline=True,
                    inputStyle={'margin-right': '3px'},
                    labelStyle={'margin-right': '10px'},
                    style={'margin-bottom': '12px'}
                ),

                html.Hr(),
                html.Label("Overlay SH surface:", style={'font-weight': 'bold'}),
                dcc.Checklist(
                    id='orbital-overlay-toggle',
                    options=[{'label': ' Show SH surface', 'value': 'show'}],
                    value=[],
                    style={'margin-top': '6px'}
                ),
            ], id='orbital-controls', style={'padding': '16px', 'display': 'none'}),

        ], style={'display': 'inline-block', 'vertical-align': 'top',
                  'width': f'{LEFT_W}px', 'overflow-y': 'auto', 'max-height': '700px',
                  'border-right': '1px solid #ddd'}),

        # Right column: graph
        dcc.Graph(id='sphere-graph',
                  style={'display': 'inline-block', 'vertical-align': 'top',
                         'width': GRAPH_W}),

    ]),
], style={'max-width': '1300px', 'margin': '0 auto', 'font-family': 'sans-serif'})

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output('ellipsoid-controls', 'style'),
    Output('sh-controls',        'style'),
    Output('orbital-controls',   'style'),
    Input('mode-selector', 'value')
)
def switch_panel(mode):
    shown  = {'padding': '16px'}
    hidden = {'padding': '16px', 'display': 'none'}
    return (
        shown  if mode == 'Ellipsoid'           else hidden,
        shown  if mode == 'Spherical Harmonics' else hidden,
        shown  if mode == 'Orbital'             else hidden,
    )


@app.callback(
    Output('orbital-m-checklist', 'options'),
    Output('orbital-m-checklist', 'value'),
    Input('orbital-l-selector', 'value'),
)
def update_m_options(l):
    l = int(l) if l is not None else 1
    options = [{'label': f' {m}', 'value': m} for m in range(-l, l + 1)]
    return options, [0]


@app.callback(
    Output('sh-sliders-container', 'children'),
    Input('lmax-input', 'value'),
    Input('r0-slider', 'value'),
    State({'type': 'sh-coeff', 'l': ALL, 'm': ALL}, 'value'),
    State({'type': 'sh-coeff', 'l': ALL, 'm': ALL}, 'id'),
)
def generate_sh_sliders(L_max, r0, current_values, current_ids):
    if L_max is None:
        return []

    L_max = int(L_max)
    bound = float(r0) if r0 is not None else 1.0
    step  = round(bound / 50, 3)
    pairs = [(l, m) for l in range(L_max + 1) for m in range(-l, l + 1)]

    saved = {(id_['l'], id_['m']): val
             for id_, val in zip(current_ids, current_values)
             if val is not None}

    return [
        html.Div([
            html.Label(f'Y_{l}^{{{m}}}:'),
            dcc.Slider(
                id={'type': 'sh-coeff', 'l': l, 'm': m},
                min=-bound, max=bound,
                value=float(np.clip(saved.get((l, m), 0.0), -bound, bound)),
                step=step,
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ], style={'margin-bottom': '15px'})
        for l, m in pairs
    ]


@app.callback(
    Output('sh-coeffs-store', 'data'),
    Input({'type': 'sh-coeff', 'l': ALL, 'm': ALL}, 'value'),
)
def collect_sh_coeffs(values):
    return [float(v) if v is not None else 0.0 for v in values]


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
    Input('sh-coeffs-store', 'data'),
    Input('orbital-l-selector', 'value'),
    Input('orbital-m-checklist', 'value'),
    Input('orbital-overlay-toggle', 'value'),
)
def update_graph(mode, a, b, c, theta_max, phi_max,
                 L_max, r0, coeff_values,
                 orb_l, orb_m_list, overlay):

    theta_val = theta_max if theta_max is not None else 2*np.pi
    phi_val   = phi_max   if phi_max   is not None else np.pi
    thetaGrid, phiGrid = create_mesh(theta_val, phi_val, resolution=100)

    surfaces = []

    # ── primary surface ──────────────────────────────────────────────────────
    if mode == 'Ellipsoid':
        x, y, z = ellipticalSurface(a or 1, b or 1, c or 1, thetaGrid, phiGrid)
        title = f'Ellipsoid: a={a:.1f}, b={b:.1f}, c={c:.1f}'
        surfaces.append(go.Surface(x=x, y=y, z=z, colorscale='Brwnyl', showscale=False))

    elif mode == 'Spherical Harmonics':
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
            title = f'SH Surface: L_max={lmax_int}, r₀={r_val:.1f}, {non_zero} active terms'
        surfaces.append(go.Surface(x=x, y=y, z=z, colorscale='Brwnyl', showscale=False))

    else:  # Orbital
        l_val  = int(orb_l) if orb_l is not None else 1
        m_list = [int(np.clip(int(m), -l_val, l_val)) for m in orb_m_list] if orb_m_list else [0]
        opacity = 0.85 if len(m_list) > 1 else 1.0

        # compute all orbitals first so we can measure their joint extent
        computed = [(orbitalSurface(l_val, m, thetaGrid, phiGrid)) for m in m_list]

        for cx, cy, cz, cY in computed:
            surfaces.append(go.Surface(x=cx, y=cy, z=cz, surfacecolor=cY,
                                       colorscale='RdBu', showscale=False,
                                       opacity=opacity))

        m_str = ', '.join(str(m) for m in m_list)
        title = f'Orbital: l={l_val},  m = [{m_str}]'

        # ── optional SH overlay ──────────────────────────────────────────────
        if overlay and 'show' in overlay:
            sh_lmax   = int(L_max) if L_max is not None else None
            sh_r0     = float(r0)  if r0    is not None else 1.0
            sh_coeffs = [float(v) if v is not None else 0.0 for v in coeff_values]
            expected  = (sh_lmax + 1) ** 2 if sh_lmax is not None else 0

            if sh_lmax is not None and len(sh_coeffs) == expected and expected > 0:
                sx, sy, sz = sphericalHarmonicSurface(sh_lmax, sh_coeffs, sh_r0,
                                                      thetaGrid, phiGrid)
            else:
                sx = sh_r0 * np.sin(phiGrid) * np.cos(thetaGrid)
                sy = sh_r0 * np.sin(phiGrid) * np.sin(thetaGrid)
                sz = sh_r0 * np.cos(phiGrid)

            # scale SH surface to match the orbital extent
            sh_extent  = np.max(np.sqrt(sx**2 + sy**2 + sz**2))
            orb_extent = max((np.max(np.sqrt(cx**2 + cy**2 + cz**2))
                              for cx, cy, cz, _ in computed), default=0.5)
            scale = (orb_extent / sh_extent) if sh_extent > 0 else 1.0
            surfaces.append(go.Surface(x=sx*scale, y=sy*scale, z=sz*scale,
                                       colorscale='Brwnyl', showscale=False, opacity=0.4))

    fig = go.Figure(data=surfaces)
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
