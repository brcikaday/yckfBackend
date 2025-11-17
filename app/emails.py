from flask_mail import Message
from app import mail
from app import app
from threading import Thread


def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Thread(target=send_async_email, args=(app,msg,)).start()
    mail.send(msg)
    
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    
    # 🔗 The link should point to your React frontend route
    reset_link = f"http://localhost:5173/reset-password?token={token}"

    subject = "Reset Your Password"
    sender = app.config["MAIL_DEFAULT_SENDER"]
    recipients = [user.email]

    text_body = f"""
    Hi {user.fullname},

    You requested to reset your password.
    Please click the link below to reset it:

    {reset_link}

    If you didn’t request this, you can ignore this email.

    — The Support Team
    """

    html_body = f"""
    <p>Hi {user.fullname},</p>
    <p>You requested to reset your password.</p>
    <p><a href="{reset_link}">Click here to reset your password</a></p>
    <p>If you didn’t request this, you can ignore this email.</p>
    <p>— The Support Team</p>
    """

    send_email(subject, sender, recipients, text_body, html_body)
