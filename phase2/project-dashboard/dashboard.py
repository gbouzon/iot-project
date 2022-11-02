import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT
import smtplib
import imaplib
import easyimap as imap
import email

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ledPin = 21
GPIO.setup(ledPin, GPIO.OUT)

DHTPin = 17 #define the pin of DHT11 - physical pin, not GPIO pin
dht = DHT.DHT(DHTPin) #create a DHT class object
dht.readDHT11()

Motor1 = 22 # Enable Pin
Motor2 = 27 # Input Pin
Motor3 = 19 # Input Pin   04 I think would work
GPIO.setup(Motor1,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor2,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(Motor3,GPIO.OUT, initial=GPIO.LOW)

app = Dash(__name__)
img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')
humidityValue = 0
temperatureValue = 0
emailSent = False
#emailReceived = True

source_address = 'pi.iotnotificationservices@gmail.com'
dest_address = 'ga@bouzon.com.br'
password = 'uuoe gtxq zccp yzgp'
imap_srv = 'imap.gmail.com'
imap_port = 993


theme_change = ThemeChangerAIO(aio_id="theme")

offcanvas = html.Div(
    [
        dbc.Button(
            "Setting", id="open-offcanvas-backdrop",style={'padding': 0, 'border': 'none', 'background': 'none'}
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
                    dbc.Col(html.Div(dbc.Input(placeholder="username", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Temperature: ")),
                    dbc.Col(html.Div(dbc.Input(placeholder="ideal_temp", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal Humidity: ")),
                    dbc.Col(html.Div(dbc.Input(placeholder="ideal_humidity", size="md", className="mb-3", readonly=True))),
                ]),
                dbc.Row(
                [
                    dbc.Col(html.Div("Ideal light intensity: ")),
                    dbc.Col(html.Div(dbc.Input(placeholder="ideal_light_intensity", size="md", className="mb-3", readonly=True))),
                ]),
            ]),
            id="offcanvas-backdrop",
            title="User information",
            is_open=False,
        ),
    ]
)



navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(theme_change, style={'padding': 0, 'border': 'none', 'background': 'none'}),
        # dbc.NavItem(dbc.NavLink("Settings", href="#")),
        dbc.NavItem(dbc.NavLink(offcanvas))

    ],
    brand="SMARTHOME",
    brand_href="#",
    color="dark",
    dark=True,
    sticky='top'
)
ledBoxTab = html.Div(id='led-box', className='ledBox',children=[
                html.H1(children='LED'),
                html.Button(img, id='led-image', n_clicks = 0),
        ])

humidTempTab = html.Div(className='grid-container', children=[
                dbc.Row([
                    dbc.Col(html.Div(id='humidity', children=[
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
                    ])),
                    dbc.Col(html.Div(id='temperature', children=[
                        daq.Thermometer(
                        id='temperature-thermometer',
                        label='Current temperature',
                        value=temperatureValue,
                        showCurrentValue=True,
                        min=0,
                        max=100
                        )
                    ]))        
                ])
            ])

fanControlTab =  html.Div(className='grid-container',id='fan-toggle-switch', children=[
                html.Div(style={'text-align': 'center'},children=[
                    html.Img(src=app.get_asset_url('fan.png'), width='15%', height='15%')
                ]),
                daq.ToggleSwitch(
                size=100,
                id='my-toggle-switch',
                value=False,
                label='Fan Status',
                labelPosition='bottom',
                color = '#0C6E87', 
                style={
                    'margin-top': '3%'
                }
                ),
            ])

tabs = dcc.Tabs([
        dcc.Tab(className='custom-tab', label='LED Control', children=[
            ledBoxTab
        ]),
        dcc.Tab(className='custom-tab', label='Humidity & Temperature', children=[
            humidTempTab
        ]),
        dcc.Tab(className='custom-tab', label='Fan Control', children=[
            fanControlTab
        ]),
    ], colors={
        "border": "#14397d",
        "primary": "#77b5b9",
        "background": "#d7eaf3"
    })



app.layout = html.Div(id="theme-switch-div", children=[
    navbar,
    html.H1(children='Welcome to IoT Dashboard', style={'text-align': 'center', 'margin-top': '3%'}),

    html.Div(className='grid-container', style={'margin': '5% 7% 5% 7%'}, children=[
        tabs
    ]),
    dcc.Interval(id='interval-component', interval=1*1500, n_intervals=0)
])

def send_email(subject, body):
    smtp_srv = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = source_address
    smtp_pass = password

    msg = 'Subject: {}\n\n{}'.format(subject, body)
    server = smtplib.SMTP(smtp_srv, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, dest_address, msg)
    server.quit()
    
def receive_email():
    #global emailReceived
    mail = imaplib.IMAP4_SSL(imap_srv)
    mail.login(source_address, password)
    mail.select('inbox')
    status, data = mail.search(None, 
    'UNSEEN', 
    'HEADER SUBJECT "Temperature is High"',
    'HEADER FROM "' + dest_address +  '"')

    mail_ids = []
    for block in data:
        mail_ids += block.split()
    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                mail_from = message['from']
                mail_subject = message['subject']
                if message.is_multipart():
                    mail_content = ''
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload().lower()
                print(mail_content)
                return "yes" in mail_content.lower()
                '''
                #if 'yes' in mail_content:
                    #return True
                #elif 'no' in mail_content:
                    emailReceived = False
                    return True
                else:
                    return False
                    '''

@app.callback(Output('led-image', 'children'),
              Input('led-image', 'n_clicks')
                )
def update_output(n_clicks):
    if n_clicks % 2 == 1:
        GPIO.output(ledPin, GPIO.HIGH)
        img = html.Img(src=app.get_asset_url('lightbulb_on.png'), width='100px', height='100px')
        return img
    else:
        GPIO.output(ledPin, GPIO.LOW)
        img = html.Img(src=app.get_asset_url('lightbulb_off.png'),width='100px', height='100px')
        return img
    
def main():
    app.run_server(debug=True, host='localhost', port=8050)
    

@app.callback(Output('fan-toggle', 'value'),
              Input('fan-toggle', 'value')
)
def toggle_fan(value):
    if value:
        GPIO.output(Motor1, GPIO.HIGH)
        value = True
    else:
         GPIO.output(Motor1, GPIO.LOW)
         value = False
    return value


@app.callback(Output('humidity-gauge', 'value'),
              Output('temperature-thermometer', 'value'),
              Input('interval-component', 'n_intervals'))
def update_sensor(n):
    global emailSent
    dht.readDHT11()
    temperatureValue = dht.temperature
    if temperatureValue > 24 and not emailSent:
        send_email("Temperature is High", "Would you like to start the fan?")
        emailSent = True
        #emailReceived = False
    elif receive_email():
        toggle_fan(True)
        time.sleep(5)
        toggle_fan(False)
    elif temperatureValue < 22:
        toggle_fan(False)
        emailSent = False
        
    humidityValue = dht.humidity
    return humidityValue, temperatureValue
  
main()
