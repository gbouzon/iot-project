import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(40, GPIO.OUT)

DHTPin = 11 #define the pin of DHT11 - physical pin, not GPIO pin
dht = DHT.DHT(DHTPin) #create a DHT class object

app = Dash(__name__)
img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')
humidityValue = 0
temperatureValue = 0


app.layout = html.Div(children=[
    html.H1(children='IoT Dashboard', style={'text-align': 'center'}),
    html.Div(className='container', id='led-box', children=[
        html.H1(children='LED Control'),
        html.Button(img, id='led-image', n_clicks = 0)
    ]),
    html.Div(className='container', id='humidity-and-temperature', children=[
        html.H1(children='Humidity & Temperature'),
        daq.Gauge(
        id='humidity-gauge',
        label='Current Humidity',
        value=humidityValue,
        max=100,
        min=0
    )
    ]), 
    daq.Thermometer(
        id='temperature-thermometer',
        label='Current temperature',
        value=5,
        min=0,
        max=100,
        style={
            'margin-top': '10%',
            'margin-bottom': '10%'
        }
    ),
    dcc.Interval(id='interval-component', interval=1*1500, n_intervals=0)
])

@app.callback(Output('led-image', 'children'),
              Input('led-image', 'n_clicks')
              )
def update_output(n_clicks):
    if n_clicks % 2 == 1:
        GPIO.output(40, GPIO.HIGH)
        img = html.Img(src=app.get_asset_url('lightbulb_on.png'), width='100px', height='100px')
        return img
    else:
        GPIO.output(40, GPIO.LOW)
        img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')
        return img
    
def main():
    app.run_server(debug=True, host='localhost', port=8050)


@app.callback(Output('humidity-gauge', 'value'),
              Output('temperature-thermometer', 'value'),
              Input('interval-component', 'n_intervals'))
def update_sensor(n):
    dht.readDHT11()
    temperatureValue = dht.temperature
    humidityValue = dht.humidity
    return humidityValue, temperatureValue

main()

