import dash.dependencies
import dash_daq as daq
from dash import html, Input, Output, dcc, Dash
import dash_bootstrap_components as dbc
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


app.layout = html.Div(children=[
    html.H1(children='IoT Dashboard', style={'text-align': 'center', 'margin-left': '2%', 'margin-bottom': '5%'}),
    html.Div( id='led-box', style={'margin-left': '2%', 'margin-top': '5%', 'margin-bottom': '5%', 'text-align':'center'},children=[
        html.H1(children='LED Control'),
        html.Button(img, id='led-image', n_clicks = 0),
    ]),

    html.Div(className='grid-container', id='humidity-and-temperature', style={'text-align':'center','margin-left': '2%', 'margin-top': '5%', 'margin-bottom': '5%'}, children=[
        html.H1(children='Humidity & Temperature'),
    ]),


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
            max=100,
            style={
                'margin-top': '5%',
                'margin-bottom': '5%'
            })])),
        ]),
    daq.ToggleSwitch(
        id='fan-toggle',
        value= False,
        label=['Fan OFF', 'Fan ON'],
        labelPosition='bottom'
),
 
    dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0)
],  style={'backgroundColor':'#B7CBC0', 'padding-top': '2%'})


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
