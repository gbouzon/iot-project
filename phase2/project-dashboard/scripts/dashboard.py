import dash
import dash.dependencies
import dash_daq as daq
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

def createDash():
    app = dash.Dash(meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = html.Div(children=[
        html.H1(children='IoT Dashboard'),
        html.Div(id='led-box', children=[
            html.H1(children=True, style={'text-align': 'center'}),
            html.Img(id='led-image', src=dash.get_asset_url('lighbulb_off.png'), style={'width': '100px', 'height': '100px'}),
            daq.LEDDisplay(
                id='light-display',
                value=30,
                style={'margin-top': '20px', 'text-align': 'center', 'display': 'block'},
            ),
        ]),
    ])
    return app

def main():
    app = createDash()
    app.run_server(debug=True, host='localhost', port=4890)
    
main()

