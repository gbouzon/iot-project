from email.message import EmailMessage
import ssl
import smtplib

def sendMail(email_receiver, subject ,body):
    #variable with email sender
    email_sender = "danichhang@gmail.com";
    email_password = "ivtinrmrsxoxemdr";

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    #Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        #login into the sender email
        smtp.login(email_sender, email_password)
        #send the email
        smtp.sendmail(email_sender, email_receiver, em.as_string())
