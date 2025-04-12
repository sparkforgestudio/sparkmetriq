import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.example.com"  # Remplace avec ton serveur SMTP
SMTP_PORT = 587
SMTP_USER = "your-email@example.com"
SMTP_PASSWORD = "your-password"

async def send_reset_email(email: str, reset_token: str):
    msg = EmailMessage()
    msg["Subject"] = "Password Reset Request"
    msg["From"] = SMTP_USER
    msg["To"] = email
    reset_link = f"https://yourdomain.com/reset-password?token={reset_token}"
    
    msg.set_content(f"Click the link to reset your password: {reset_link}")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
