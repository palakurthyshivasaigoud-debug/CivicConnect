import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(to_email: str, subject: str, body: str):
    if not (config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASS and config.FROM_EMAIL):
        # SMTP not configured, skip
        print("SMTP not configured — skipping email send.")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = config.FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.sendmail(config.FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
