import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21, GPIO.OUT)


app = Dash(__name__)
img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')


app.layout = html.Div(children=[
    html.H1(children='IoT Dashboard'),
    html.Div(id='led-box', children=[
        html.H1(children=True, style={'text-align': 'center'}),
        html.Button(img, id='led-image', n_clicks = 0)
    ]),
])


@app.callback(Output('led-image', 'children'),
              Input('led-image', 'n_clicks'))
def update_output(n_clicks):
    if n_clicks % 2 == 1:
        GPIO.output(21, GPIO.HIGH)
        img = html.Img(src=app.get_asset_url('lightbulb_on.png'), width='100px', height='100px')
        return img
    else:
        GPIO.output(21, GPIO.LOW)
        img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')
        return img
    

def main():
    app.run_server(debug=True, host='localhost', port=8050)
    
main()

