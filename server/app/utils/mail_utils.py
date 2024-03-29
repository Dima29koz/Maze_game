from flask import render_template
from flask_mail import Message

from server.app import mail
from server.app.api_user_account.models import User


def send_email(subject: str, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_email_confirmation_mail(user: User, origin: str):
    if not user.user_email:
        return
    token = user.get_token('confirm_email')
    link = f'{origin}/confirm_email?token={token}'
    send_email('[MazeGame] Confirm Your Email',
               recipients=[user.user_email],
               text_body=render_template('email/confirm_email.txt',
                                         user=user, link=link),
               html_body=render_template('email/confirm_email.html',
                                         user=user, link=link))


def send_password_reset_email(user: User, origin: str):
    if not user.user_email:
        return
    token = user.get_token('reset_password')
    link = f'{origin}/reset_password?token={token}'
    send_email('[MazeGame] Reset Your Password',
               recipients=[user.user_email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, link=link),
               html_body=render_template('email/reset_password.html',
                                         user=user, link=link))
