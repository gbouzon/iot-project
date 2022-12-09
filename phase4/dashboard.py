import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash_bootstrap_templates import ThemeChangerAIO
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
import smtplib
import imaplib
import easyimap as imap
import email
from Emails import *  
from scanner import *
#import paho.mqtt.client as mqtt
import random
from paho.mqtt import client as mqtt_client
from datetime import datetime
#This is to set time in specific timezone otherwise it gives time 2 hours in advance
import pytz

import sqlite3
from sqlite3 import Error

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ledPin = 21
GPIO.setup(ledPin, GPIO.OUT)

DHTPin = 17 #define the pin of DHT11
dht = DHT.DHT(DHTPin) #create a DHT class object
dht.readDHT11()

Motor1 = 22 # Enable Pin
Motor2 = 27 # Input Pin
Motor3 = 19 # Input Pin  
GPIO.setup(Motor1,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor2,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(Motor3,GPIO.OUT, initial=GPIO.LOW)


global current_light_intensity
current_light_intensity = "NaN"

global no_current_devices
no_current_devices = "NaN"

global tagID, username, uTempThreshold, uHumidityThreshold, uLightIntensity
tagID = "NaN"
username = ""
uTempThreshold = 0.0
uHumidityThreshold = 0
uLightIntensity = 0

# This works as long as the arduino code is running (change broker)
broker = '192.168.0.70'
# broker = '172.20.10.14'

port = 1883
topic = "/IoTlab/status"
topic2 = "/IoTlab/readTag"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


app = Dash(__name__)
theme_change = ThemeChangerAIO(aio_id="theme",  radio_props={"persistence": True,  "value": dbc.themes.LUX});


img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='53%', height='53%')
userPhoto = html.Img(src=app.get_asset_url('avatar.png'),width='15%', height='15%', style={'border-radius': '50%'})
humidityValue = 0
temperatureValue = 0
tempUnit = 'Celsius'
emailSent = False
emailReceived = 0
flag = False


source_address = 'pi.iotnotificationservices@gmail.com'
dest_address = 'ga@bouzon.com.br'
password = 'uuoe gtxq zccp yzgp'
imap_srv = 'imap.gmail.com'
imap_port = 993


theme_change = ThemeChangerAIO(aio_id="theme");


offcanvas = html.Div(
    [
        dbc.Button(
            userPhoto, id="open-offcanvas-backdrop",style={'padding': 0, 'border': 'none', 'background': 'none'}
        ),
        dbc.Offcanvas(
            html.Div(
            [                       
                html.Div(style={'text-align': 'center'},children=[
                      html.Img(src=app.get_asset_url('avatar.png'), width='50%', height='50%', style={'border-radius': '50%'})
            ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Name: ")),
                    dbc.Col(html.Div(dbc.Input(id="username", placeholder="username", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Temperature: ")),
                    dbc.Col(html.Div(dbc.Input(id="tempThreshold",placeholder="ideal_temp", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Humidity: ")),
                    dbc.Col(html.Div(dbc.Input(id="humidityThreshold",placeholder="ideal_humidity", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal light intensity: ")),
                    dbc.Col(html.Div(dbc.Input(id='lightIntensity',placeholder="ideal_light_intensity", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [   
                    dbc.Col(html.Div(theme_change, style={'padding': 0, 'border': 'none', 'background': 'none'})),
                ])
            ]),
            id="offcanvas-backdrop",
            title="User information",
            is_open=False,
        ),
    ]
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(offcanvas), style={'text-align': 'end'})
    ],
    brand="SMARTHOME",
    brand_href="#",
    color="dark",
    dark=True,
    sticky='top'
)

cardLedBox = dbc.Card([
    dbc.CardHeader([
        html.H4("LED", className="card-title, text-center")
    ]),
    dbc.CardBody([
        html.Button(img, id='led-image', n_clicks = 0, className = "btn btn-primary-outline"),
        html.Div(children='Click the image to turn on the LED', style = {'font-size': '12px'})
    ]), 
], color="dark", outline=True);

cardLighIntensity = dbc.Card([
    dbc.CardHeader([
        html.H4("Light Intensity", className="card-title, text-center")
    ]),
    dbc.CardBody([
        html.H5("Current Light Intensity", className="card-title"),
        html.Img(src=app.get_asset_url('light_intensity.png'),width='30%', height='31%'),
                dbc.Input(
                    size="sm",
                    id='light-intensity-value',
                    className="mb",
                    value="The light intensity is " + str(current_light_intensity), 
                    readonly = True,
                    style = {
                        'text-align': 'center'
                    }
                )
    ]), 
],color="dark", outline=True);

cardTemp = dbc.Card([
    dbc.CardHeader([
        html.H4("Humidity", className="card-title, text-center")
    ]),
    dbc.CardBody([
        html.Div(id='humidity', children=[
                        daq.Gauge(
                        color={"gradient":True,"ranges":{"yellow":[0,30],"green":[30,50],"red":[50,100]}},
                        id='humidity-gauge',
                        label='Current Humidity',
                        showCurrentValue=True,
                        units="Percentage",
                        value=humidityValue,
                        max=100,
                        min=0
                        
                        )
                    ])
    ]), 
],color="dark", outline=True);

cardHumid = dbc.Card([
    dbc.CardHeader([
        html.H4("Temperature", className="card-title, text-center")
    ]),
    dbc.CardBody([
        html.Div(id='temperature', children=[
                        daq.Thermometer(
                        id='temperature-thermometer',
                        label='Current temperature',
                        value=temperatureValue,
                        showCurrentValue=True,
                        min=-20,
                        max=122
                        ),
                        daq.ToggleSwitch(
                        size=40,
                        id='temp-toggle',
                        value=False,
                        label=['Celsius', 'Fahrenheit'],
                        labelPosition='bottom',
                        color = '#0C6E87',
                        style={
                            "margin": "5%"
                        }
                        
                        )
                    ])
    ]), 
],color="dark", outline=True);

cardFanControlTab= dbc.Card([
    dbc.CardHeader([
        html.H4("Fan Status", className="card-title, text-center")
    ]),
    dbc.CardBody([
        html.Img(id='fan_picture',src=app.get_asset_url('fan.png'),width='35%', height='35%', 
                style={
                    "margin": "5%"
                } 
                ),
        daq.ToggleSwitch(
                size=40,
                id='fan-toggle',
                value=False,
                label=['off', 'on'],
                labelPosition='bottom',
                color = '#0C6E87', 
                style={
                    "margin": "2%"
                }
                )
    ]), 
], color="dark", outline=True);

bluetoothDevicesCard = dbc.Card([
        dbc.CardHeader([
            html.H4("Detect Bluetooth devices", className="card-title"),
        ]),
        dbc.CardBody(
            [
                dbc.Input(
                    size="sm",
                    id = "bluetooth-devices-input",
                    className="mb-2",
                    value="Bluetooth devices nearby: " + str(no_current_devices),
                    readonly = True,
                    style = {
                        'text-align': 'center',
                    }
                ),
                html.Div(children=[
                    dcc.Input(id='input-on-submit',type='text', style={'width':'50%', 'margin-right': '4%'}),
                    html.Button('Submit', id='submit-val', n_clicks=0) ], style={'margin-top': '7%'}),
                    html.Div(id='container-button-basic', children='Enter a value and press submit', style = {'font-size': '12px'})
                
            ]
        )
    ],
    color="dark", outline=True, style ={'padding-bottom': '9%'} 
)

content = html.Div([
            navbar, 
            html.H1(children='Welcome to IoT Dashboard', style={'text-align': 'center', 'margin': '3rem'}),
            dbc.Container([
                dbc.Row([
                    dbc.Col(html.Div([
                            dbc.Row([
                                dbc.Col(cardLedBox, width=6, align="start", className="h-100"),
                                dbc.Col(cardFanControlTab, width=6 ,align="start", className="h-100")
                                ], style = {'height': '100%', 'padding-bottom': '4%'}),
                            dbc.Row([
                                dbc.Col(cardLighIntensity, width=6 ,align="start", className="h-100"),
                                dbc.Col(bluetoothDevicesCard,  width=6 ,align="start", className="h-100")
                                ], style = {'height': '100%', 'padding-bottom': '4%'}),

                 ])),
                    dbc.Col(dbc.Row([
                                dbc.Col(cardTemp, width=6 ,align="start", className="h-100"),
                                dbc.Col(cardHumid,  width=6 ,align="start", className="h-100")
                                ], style = {'height': '100%', 'padding-bottom': '4%'}))

                    ])
                                          
                ]),
            # ])     
        ], className="content");

app.layout = html.Div(id="theme-switch-div", children=[
    content,
    dcc.Interval(id='interval-component', interval=3*1000, n_intervals=0)
    ]);
    
@app.callback(
    Output('container-button-basic', 'children'),
    Output('bluetooth-devices-input', 'value'),
    Input('submit-val', 'n_clicks'),
    State('input-on-submit', 'value')
)
def update_output(n_clicks, value):
    global no_current_devices
    if value is None:
        no_current_devices = "None"
    else:
        no_current_devices = scan(int(value))
    return 'The RSSI is > "{}"'.format(
        value
    ), "Bluetooth devices nearby: " + str(no_current_devices)

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

@app.callback(Output('led-image', 'children'),
              Input('led-image', 'n_clicks')
                )
def update_output(n_clicks):
    if n_clicks % 2 == 1:
        GPIO.output(ledPin, GPIO.HIGH)
        img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='53%', height='53%')
        return img
    else:
        GPIO.output(ledPin, GPIO.LOW)
        img = html.Img(src=app.get_asset_url('lightbulb_on.png'),width='53%', height='53%')
        return img
       

@app.callback(Output('fan-toggle', 'value'),
              Input('fan-toggle', 'value')
)
def toggle_fan(value):
    if value:
        GPIO.output(Motor1, GPIO.HIGH)
        value = True
        # fanPicture = app.get_asset_url('fan_on.png')
    else:
         GPIO.output(Motor1, GPIO.LOW)
         value = False
        #  fanPicture = app.get_asset_url('fan.png')
    return value


@app.callback(Output('humidity-gauge', 'value'),
              Output('temperature-thermometer', 'value'),
              Output('temperature-thermometer', 'units'),
              Input('interval-component', 'n_intervals'),
              Input('temp-toggle', 'value'))
def update_sensor(n, tValue):
    global emailSent, emailReceived, uTempThreshold
    emailReceivedContent = receive_email();
    dht.readDHT11()
    temperatureValue = dht.temperature
    if temperatureValue > float(uTempThreshold) and not emailSent:
        send_email("Temperature is High", "Would you like to start the fan?")
        emailSent = True
    elif emailReceivedContent is not None and emailReceived < 1:
        emailReceived = 1
        if emailReceivedContent == "yes":
            toggle_fan(True)
            time.sleep(5)
            toggle_fan(False)
    elif temperatureValue < 22:
        toggle_fan(False)
        emailSent = False
        emailReceived = 0
        
    humidityValue = dht.humidity

    # for toggle switch: C to F
    if tValue:
        tempUnit = 'Fahrenheit'
        temperatureValue = temperatureValue * (9/5) + 32
    elif not tValue:
        tempUnit = 'Celsius'

    return humidityValue, temperatureValue, tempUnit


#Phase 3 code
@app.callback(
    Output("offcanvas-backdrop", "is_open"),
    Input("open-offcanvas-backdrop", "n_clicks"),
    State("offcanvas-backdrop", "is_open"))
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global username, uTempThreshold, uHumidityThreshold, uLightIntensity, flag 
        if (msg.topic == topic):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

            if(int(msg.payload.decode()) <= int(uLightIntensity)) :
                GPIO.output(ledPin, GPIO.HIGH)
                if(not flag):
                    time = datetime.now(pytz.timezone('America/New_York'))
                    currtime = time.strftime("%H:%M")
                    send_email("Light", "The Light is ON")
                    flag = True
                
            else:
                GPIO.output(ledPin, GPIO.LOW)
                flag = False
                
            global current_light_intensity
            current_light_intensity = msg.payload.decode()
        
        if (msg.topic == topic2):
            print(f"Received tag: `{msg.payload.decode()}` from `{msg.topic}` topic")
            global tagID
            tagID = msg.payload.decode()
            logIn()
            
    client.subscribe(topic)
    client.subscribe(topic2)
    client.on_message = on_message


@app.callback(Output('light-intensity-value', 'value'),
              Output('username', 'value'),
              Output('tempThreshold', 'value'),
              Output('humidityThreshold', 'value'),
              Output('lightIntensity', 'value'),
              Input('interval-component', 'n_intervals'))
def update_light_intensity_user_info(n):
    return 'The  light intensity is:' + str(current_light_intensity), username, uTempThreshold, uHumidityThreshold, uLightIntensity

def logIn():
    global username, uTempThreshold, uHumidityThreshold, uLightIntensity 
    db_file = "smarthome_db"
    conn = create_connection(db_file)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE userID = ?", [tagID])
        user = cur.fetchone()
        
        if not user:
            print("log in failed")
        else:
            username = user[1]
            uTempThreshold = user[2]
            uHumidityThreshold = user[3]
            uLightIntensity = user[4]
#             str, str, float, int, int
#             userID, name, tempThreshold, humidityThreshold, lightIntensityThreshold
            print(username, uTempThreshold, uHumidityThreshold, uLightIntensity)
    
            time = datetime.now(pytz.timezone('America/New_York'))
            currtime = time.strftime("%H:%M")
            send_email("Log In", username + " entered at " + currtime)
            
    finally:
        cur.close()
        
def main():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    app.run_server(debug=True, host='localhost', port=8050)    
  
main()

