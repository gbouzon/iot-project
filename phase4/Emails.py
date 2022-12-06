from email.message import EmailMessage
import ssl
import smtplib
import email
import imaplib
from datetime import datetime
import pytz

EMAIL = "danichhang@gmail.com";
PASSWORD = "ivtinrmrsxoxemdr";
SERVER = 'imap.gmail.com'

source_address = 'pi.iotnotificationservices@gmail.com'
#source_address = 'danichhang@gmail.com';
dest_address = 'ga@bouzon.com.br';
#password = 'ivtinrmrsxoxemdr';
password = 'uuoe gtxq zccp yzgp'
imap_srv = 'imap.gmail.com'
imap_port = 993

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
                return "yes" if "yes" in mail_content.lower() else "no"

