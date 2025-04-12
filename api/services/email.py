import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "ton-email@gmail.com"
SMTP_PASSWORD = "ton-mot-de-passe"

async def send_password_reset_email(to_email: str, reset_link: str):
    """ Envoie un email avec le lien de réinitialisation """
    msg = EmailMessage()
    msg["Subject"] = "Réinitialisation de votre mot de passe"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}\n\nCe lien expire dans 15 minutes.")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
