import smtplib
from email.mime.text import MIMEText
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"✅ Email sent to {to_email}")
