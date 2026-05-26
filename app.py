import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ALL

from mesh import mesh as create_mesh
from ellipticalSurface import ellipticalSurface
from sphericalHarmonicSurface import sphericalHarmonicSurface
from orbitalSurface import orbitalSurface

app = Dash(__name__)
server = app.server

_dim = {'color': '#888', 'font-size': '0.85em', 'margin': '4px 0 12px 0'}

# Store for SH coefficients, avoids mixing pattern-matched ALL inputs with
# list-valued checklist inputs in the same callback (Dash 4 dispatcher bug).
_sh_coeff_store = dcc.Store(id='sh-coeffs-store', data=[])

LEFT_W  = 480
GRAPH_W = f'calc(100% - {LEFT_W + 20}px)'

# Two-tone palettes for orbital lobes: (negative_lobe, positive_lobe).
# Cool/warm pairs so the sign axis is consistent across orbitals while each m
# still gets a distinct hue. Indexed by `m % len(LOBE_PALETTES)` so a given m
# always renders in the same colors regardless of which other m's are selected.
LOBE_PALETTES = [
    ('#2c5aa0', '#a02c2c'),   # blue   / red      (m ≡ 0)
    ('#177a6e', '#a36117'),   # teal   / orange   (m ≡ 1)
    ('#5a3a8c', '#b89c1b'),   # purple / gold     (m ≡ 2)
    ('#3d7a3d', '#a33d7a'),   # green  / magenta  (m ≡ 3)
    ('#5a6b8c', '#8c5a6b'),   # slate  / rose     (m ≡ 4)
    ('#1f4e6f', '#6f3f1f'),   # navy   / brown    (m ≡ 5)
    ('#3a8c6b', '#8c3a5d'),   # sea    / wine     (m ≡ 6)
]

# Mode identifiers, internal values are kept short and stable so callbacks
# don't break when display labels are reworded.
MODE_ELLIPSOID = 'ellipsoid'
MODE_SH        = 'sh'
MODE_ORBITAL   = 'orbital'

# Single source of truth for the reference-sphere visual style — used in
# both SH and Orbital modes so they look identical.
REFERENCE_SPHERE_STYLE = dict(
    colorscale=[[0, '#d8d8d8'], [1, '#d8d8d8']],
    showscale=False,
    opacity=0.35,
)


def _make_sphere(radius, thetaGrid, phiGrid):
    """Return (x, y, z) for a sphere of `radius` on the given (θ, φ) mesh."""
    x = radius * np.sin(phiGrid) * np.cos(thetaGrid)
    y = radius * np.sin(phiGrid) * np.sin(thetaGrid)
    z = radius * np.cos(phiGrid)
    return x, y, z


# =============================================================================
# LAYOUT
# =============================================================================
app.layout = html.Div([
    _sh_coeff_store,
    html.H1("SEIVE",
            style={'text-align': 'center',
                   'margin-bottom': '2px',
                   'letter-spacing': '0.08em'}),
    # Inline-html dance so the backronym letters can be bolded.
    html.P(children=[
        html.Span("Sph"), html.B("E"), html.Span("rical harmon"),
        html.B("I"), html.Span("cs "),
        html.B("V"), html.Span("isualiz"), html.B("E"), html.Span("r"),
    ], style={'text-align': 'center',
              'color': '#888',
              'font-size': '0.95em',
              'margin-top': 0,
              'margin-bottom': '20px',
              'letter-spacing': '0.02em'}),

    # ── shared header controls ───────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Label("Surface Type:", style={'font-weight': 'bold'}),
            dcc.RadioItems(
                id='mode-selector',
                options=[
                    {'label': ' Ellipsoid',
                     'value': MODE_ELLIPSOID},
                    {'label': ' Sphere Deformed by Spherical Harmonics',
                     'value': MODE_SH},
                    {'label': ' Basis Functions (Orbitals)',
                     'value': MODE_ORBITAL},
                ],
                value=MODE_ELLIPSOID,
                inline=True,
                labelStyle={'margin-right': '14px'},
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

        html.Div([
            html.Label("Mesh resolution:"),
            dcc.Input(id='resolution-input', type='number',
                      value=150, min=20, max=1000, step=10,
                      style={'width': '80px', 'margin-left': '8px'}),
            html.Span(
                "  points per side, 100–200 keeps interaction snappy, "
                "500+ for stills",
                style=_dim
            ),
        ], style={'margin-top': '12px'}),
    ], style={'padding': '20px', 'border-bottom': '1px solid #ddd'}),

    # ── main body: controls left, graph right ────────────────────────────────
    html.Div([
        # Left column
        html.Div([
            # Ellipsoid panel
            html.Div([
                html.H3("Ellipsoid", style={'margin-top': 0}),
                html.P("Base shape, axes scale the sphere along X, Y, Z.",
                       style=_dim),
                html.Label("a (X-axis):"),
                dcc.Slider(id='a-slider', min=0.1, max=3, value=1, step=0.1),
                html.Label("b (Y-axis):"),
                dcc.Slider(id='b-slider', min=0.1, max=3, value=1, step=0.1),
                html.Label("c (Z-axis):"),
                dcc.Slider(id='c-slider', min=0.1, max=3, value=1, step=0.1),
            ], id='ellipsoid-controls', style={'padding': '16px'}),

            # SH-Deformed Sphere panel
            html.Div([
                html.H3("Sphere Deformed by Spherical Harmonics",
                        style={'margin-top': 0}),
                html.P("Sphere of radius r₀ deformed by Σ aₗₘ Yₗᵐ.",
                       style=_dim),
                html.Label("L_max (max degree):"),
                dcc.Input(id='lmax-input', type='number', value=2,
                          min=0, max=84, step=1,   # ← CAPPED at 84
                          style={'width': '60px', 'margin-bottom': '12px'}),
                html.Label("r₀ (base radius):"),
                dcc.Slider(id='r0-slider', min=0.5, max=2, value=1.0, step=0.1),
                html.Hr(),
                html.Label("Reference sphere:", style={'font-weight': 'bold'}),
                dcc.Checklist(
                    id='sh-overlay-toggle',
                    options=[{'label': ' Show base sphere (radius = r₀)',
                              'value': 'show'}],
                    value=[],
                    style={'margin-top': '6px', 'margin-bottom': '12px'}
                ),
                html.Hr(),
                html.Label("Coefficients aₗₘ:", style={'font-weight': 'bold'}),
                html.Div(id='sh-sliders-container')
            ], id='sh-controls', style={'padding': '16px', 'display': 'none'}),

            # Basis Functions (Orbitals) panel
            html.Div([
                html.H3("Basis Functions (Orbitals)", style={'margin-top': 0}),
                html.P("Polar plot of |Yₗᵐ|, radius is magnitude, color is sign.",
                       style=_dim),
                html.Label("l (degree):"),
                html.Div(
                    dcc.Input(
                        id='orbital-l-selector',
                        type='number', value=1, min=0, step=1,
                        style={'width': '70px'}
                    ),
                    style={'margin-bottom': '14px'}
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
                html.Label("Reference sphere:", style={'font-weight': 'bold'}),
                dcc.Checklist(
                    id='orbital-overlay-toggle',
                    options=[{'label': ' Show reference sphere', 'value': 'show'}],
                    value=[],
                    style={'margin-top': '6px'}
                ),
                html.Div([
                    html.Label("Sphere radius:"),
                    dcc.Slider(id='sphere-radius-slider',
                               min=0.1, max=3, value=1.0, step=0.05),
                ], style={'margin-top': '8px'}),
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
        shown if mode == MODE_ELLIPSOID else hidden,
        shown if mode == MODE_SH        else hidden,
        shown if mode == MODE_ORBITAL   else hidden,
    )


@app.callback(
    Output('orbital-m-checklist', 'options'),
    Output('orbital-m-checklist', 'value'),
    Input('orbital-l-selector', 'value'),
)
def update_m_options(l):
    l = int(l) if l is not None else 1
    if l < 0:
        l = 0
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
    Input('resolution-input', 'value'),
    Input('lmax-input', 'value'),
    Input('r0-slider', 'value'),
    Input('sh-coeffs-store', 'data'),
    Input('sh-overlay-toggle', 'value'),
    Input('orbital-l-selector', 'value'),
    Input('orbital-m-checklist', 'value'),
    Input('orbital-overlay-toggle', 'value'),
    Input('sphere-radius-slider', 'value'),
)
def update_graph(mode, a, b, c, theta_max, phi_max, resolution,
                 L_max, r0, coeff_values, sh_overlay,
                 orb_l, orb_m_list, orb_overlay, sphere_r):
    theta_val = theta_max if theta_max is not None else 2*np.pi
    phi_val   = phi_max   if phi_max   is not None else np.pi
    res       = int(resolution) if resolution is not None else 150
    res       = max(20, min(res, 1000))           # hard-clamp for safety
    thetaGrid, phiGrid = create_mesh(theta_val, phi_val, resolution=res)

    surfaces = []
    title    = ''

    # ── primary surface ──────────────────────────────────────────────────────
    if mode == MODE_ELLIPSOID:
        x, y, z = ellipticalSurface(a or 1, b or 1, c or 1, thetaGrid, phiGrid)
        title = f'Ellipsoid: a={a:.1f}, b={b:.1f}, c={c:.1f}'
        surfaces.append(go.Surface(x=x, y=y, z=z, colorscale='Brwnyl', showscale=False))

    elif mode == MODE_SH:
        r_val    = float(r0) if r0 is not None else 1.0
        # Enforce L_max cap again in case the input was bypassed
        lmax_int = int(L_max) if L_max is not None else None
        if lmax_int is not None and lmax_int > 84:
            lmax_int = 84
        coeffs   = [float(v) if v is not None else 0.0 for v in coeff_values]
        expected = (lmax_int + 1) ** 2 if lmax_int is not None else 0
        if lmax_int is None or not coeffs or len(coeffs) != expected:
            x, y, z = _make_sphere(r_val, thetaGrid, phiGrid)
            title = 'Sphere Deformed by SH (set L_max to add coefficients)'
        else:
            x, y, z = sphericalHarmonicSurface(lmax_int, coeffs, r_val, thetaGrid, phiGrid)
            non_zero = sum(1 for v in coeffs if abs(v) > 0.01)
            title = f'Deformed Sphere: L_max={lmax_int}, r₀={r_val:.1f}, {non_zero} active terms'

        # Determine opacity of the deformed sphere based on overlay toggle
        overlay_active = sh_overlay and 'show' in sh_overlay
        deformed_opacity = 0.75 if overlay_active else 1.0

        surfaces.append(go.Surface(
            x=x, y=y, z=z,
            colorscale='Brwnyl',
            showscale=False,
            opacity=deformed_opacity
        ))

        # ── reference sphere overlay (radius is locked to r₀) ────────────────
        if overlay_active:
            sx, sy, sz = _make_sphere(r_val, thetaGrid, phiGrid)
            surfaces.append(go.Surface(
                x=sx, y=sy, z=sz,
                name=f'base sphere r₀={r_val:.2f}',
                colorscale=[[0, '#d8d8d8'], [1, '#d8d8d8']],
                showscale=False,
                opacity=0.4,          # fully opaque
            ))
    else:  # MODE_ORBITAL
        l_val  = int(orb_l) if orb_l is not None else 1
        if l_val < 0:
            l_val = 0
        m_list = [int(np.clip(int(m), -l_val, l_val))
                  for m in (orb_m_list or [])]

        if not m_list:
            title = f'Basis Function Yₗᵐ: l={l_val}, (no m selected)'
        else:
            # Pre-compute every selected orbital. Copy grids so the routine
            # can't mutate the shared meshgrid, cast to real float in case it
            # returns complex (sph_harm does).
            computed = []
            for m in m_list:
                cx, cy, cz, cY = orbitalSurface(
                    l_val, m, thetaGrid.copy(), phiGrid.copy()
                )
                cx = np.asarray(cx, dtype=float)
                cy = np.asarray(cy, dtype=float)
                cz = np.asarray(cz, dtype=float)
                cY = np.real(np.asarray(cY)).astype(float)
                computed.append((cx, cy, cz, cY))

            for (cx, cy, cz, cY), m in zip(computed, m_list):
                # Stable color: indexed by m itself, not by position in the
                # selection list. Python's % handles negative m correctly.
                neg, pos = LOBE_PALETTES[m % len(LOBE_PALETTES)]
                vmax = float(np.nanmax(np.abs(cY))) or 1.0
                # Hard two-tone split at zero, sign of Yₗᵐ reads as one of
                # two colors per m.
                cs = [[0.0, neg], [0.499, neg], [0.501, pos], [1.0, pos]]
                surfaces.append(go.Surface(
                    x=cx, y=cy, z=cz,
                    surfacecolor=cY,
                    colorscale=cs,
                    cmin=-vmax, cmax=vmax,
                    cauto=False,
                    showscale=False,
                    opacity=1.0,          # opaque sidesteps WebGL depth-sort artifacts
                    name=f'm={m}',
                ))

            m_str = ', '.join(str(m) for m in m_list)
            title = f'Basis Functions Yₗᵐ: l={l_val},  m = [{m_str}]'

        # ── reference sphere overlay (independent of SH coefficients) ────────
        if orb_overlay and 'show' in orb_overlay:
            sr = float(sphere_r) if sphere_r is not None else 1.0
            sx, sy, sz = _make_sphere(sr, thetaGrid, phiGrid)
            surfaces.append(go.Surface(
                x=sx, y=sy, z=sz,
                name=f'sphere r={sr:.2f}',
                **REFERENCE_SPHERE_STYLE,
            ))

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