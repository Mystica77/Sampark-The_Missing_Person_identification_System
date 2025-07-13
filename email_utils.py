
# email_utils.py
import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, APP_PASSWORD

def send_alert_email(to_email, name):
    subject = "Missing Person Found!"
    body = f"The missing person {name} has been identified by the system. Please contact the concerned authorities."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
            print(f" Alert email sent to {to_email}")
    except Exception as e:
        print(f" Failed to send email: {e}")



