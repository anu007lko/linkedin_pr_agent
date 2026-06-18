import smtplib
from email.mime.text import MIMEText
import config

def send_notification(subject: str, body: str):
    """Sends an email notification via Gmail SMTP."""
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD or not config.NOTIFICATION_EMAIL:
        print("Gmail configuration is incomplete. Skipping notification.")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = config.GMAIL_ADDRESS
    msg['To'] = config.NOTIFICATION_EMAIL

    try:
        # Connect to Gmail SMTP server on port 587 using TLS
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"Notification sent: {subject}")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

if __name__ == "__main__":
    # Test
    # send_notification("Test Subject", "Test Body")
    pass
