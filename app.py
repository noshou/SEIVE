import ellipticalSurface as es
from dash import Dash, dcc, html, Input, Output
import numpy as np 

app = Dash(__name__)

# Application Layout
app.layout = html.Div([
    html.H1("Dynamic Parametric Sphere"),
    
    # Sliders for User Inputs
    html.Div([
        html.Label("Parameter a (X-axis scale):"),
        dcc.Slider(id='a-slider', min=1, max=50, value=2, step=0.5, marks={i: str(i) for i in range(1, 51, 5)}),
        
        html.Label("Parameter b (Y-axis scale):"),
        dcc.Slider(id='b-slider', min=1, max=50, value=2, step=0.5, marks={i: str(i) for i in range(1, 51, 5)}),
        
        html.Label("Parameter c (Z-axis scale):"),
        dcc.Slider(id='c-slider', min=1, max=50, value=2, step=0.5, marks={i: str(i) for i in range(1, 51, 5)}),

        html.Label("Max Theta (Azimuth Angle):"),
        dcc.Slider(id='theta-slider', min=0.1, max=2*np.pi, value=2*np.pi, step=0.1, marks={0: '0', 3.14: 'π', 6.28: '2π'}),
        
        html.Label("Max Phi (Inclination Angle):"),
        dcc.Slider(id='phi-slider', min=0.1, max=np.pi, value=np.pi, step=0.1, marks={0: '0', 1.57: 'π/2', 3.14: 'π'}),
    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'}),
    
    # The Graph Container
    html.Div([
        dcc.Graph(id='sphere-graph')
    ], style={'display': 'inline-block'})
])

# Reactive Callback Logic
@app.callback(
    Output('sphere-graph', 'figure'),
    Input('a-slider', 'value'),
    Input('b-slider', 'value'),
    Input('c-slider', 'value'),
    Input('theta-slider', 'value'),
    Input('phi-slider', 'value')
)
def update_graph(a, b, c, theta_max, phi_max):
    # Call your imported custom function from ellipticalSurface.py
    fig = es.ellipticalSurface(
        a=a, 
        b=b, 
        c=c, 
        thetaMax=theta_max, 
        phiMax=phi_max
    )
    
    # Force a fixed coordinate box size so the ellipsoid 
    # doesn't auto-zoom and always appear the same size.
    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=30), # Eliminates empty border padding
        scene=dict(
            # REMOVED: xaxis/yaxis/zaxis fixed ranges
            aspectmode='data' # Maintains true 1:1 mathematical proportions
        )
    )    
    return fig

if __name__ == '__main__':
    app.run(debug=True)
