from flask_mail import Message
from app import mail
from app import app
from threading import Thread
from app.models import AuditLog


import os
import resend

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY")


# Generic email sender using Resend
def send_email(subject, to, text_body, html_body):
    try:
        response = resend.Emails.send({
            "from": "YCKF <no-reply@resend.dev>",   # Use your domain if you have one
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": text_body
        })
        print("Resend email response:", response)
        return True

    except Exception as e:
        print("Email sending failed:", e)
        return False


# Password reset email
def send_password_reset_email(user):
    token = user.get_reset_password_token()

    # React frontend reset URL
    reset_link = f"https://yckf-app.vercel.app/reset-password?token={token}"

    subject = "Reset Your Password"
    to = user.email

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

    send_email(subject, to, text_body, html_body)



import resend

def send_donation_email(user, amount, reference):
    subject = "Donation Successful"
    to = user.email

    text_body = f"""
    Hello {user.fullname},

    Thank you for your generous donation of GHS {amount:.2f}.
    Your payment has been confirmed and your access is now unlocked.

    Reference ID: {reference}

    Best regards,
    The Team
    """

    html_body = f"""
    <p>Hello {user.fullname},</p>
    <p>Thank you for your generous donation of <strong>GHS {amount:.2f}</strong>.</p>
    <p>Your payment has been confirmed and your access is now unlocked.</p>
    <p><strong>Reference ID:</strong> {reference}</p>
    <p>Best regards,<br>The Team</p>
    """

    try:
        resend.Emails.send({
            "from": "YCKF <no-reply@resend.dev>",
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": text_body
        })
        print("Donation email sent successfully")

    except Exception as e:
        print(f"Failed to send donation email: {e}")
