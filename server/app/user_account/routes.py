from flask import request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, current_user, logout_user

from . import user_account
from .. import login_manager
from ..main.models import get_user_by_name, User
from ..utils.hider import get_hidden_email
from ..utils.mail_utils import send_password_reset_email, send_email_confirmation_mail


@login_manager.unauthorized_handler
def unauthorized():
    if request.blueprint == 'user_account':
        return jsonify('login required'), 401
    else:
        flash(login_manager.login_message, login_manager.login_message_category)
        return redirect(url_for(login_manager.login_view))


@user_account.route('/login', methods=["POST"])
def login():
    request_data = request.get_json()
    user = get_user_by_name(request_data.get('username'))
    if not user or not user.check_password(request_data.get('pwd')):
        return jsonify(msg='Wrong username or password'), 401

    remember = request_data.get('remember')
    login_user(user, remember=remember)
    return jsonify(msg='login successful')


@user_account.route('/profile_settings')
@login_required
def profile_settings():
    return jsonify(
        id=current_user.id,
        username=current_user.user_name,
        email=get_hidden_email(current_user.user_email),
        is_email_verified=current_user.is_email_verified,
    )


@user_account.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return jsonify('already authenticated'), 403

    request_data = request.get_json()
    user = get_user_by_name(request_data.get('username'))
    if user:
        send_password_reset_email(user, request.headers.get('X-ORIGIN'))
    return jsonify(msg='Проверьте вашу почту и следуйте инструкциям для сброса пароля')


@user_account.route('/reset_password', methods=['POST'])
def reset_password():
    if current_user.is_authenticated:
        return jsonify('already authenticated'), 403

    request_data = request.get_json()
    user = User.verify_token(request_data.get('token'), 'reset_password')
    if not user:
        return jsonify(msg='Wrong token'), 400

    new_pwd = request_data.get('pwd')
    new_pwd_repeat = request_data.get('pwd_repeat')
    if new_pwd == new_pwd_repeat:
        user.set_pwd(new_pwd)
        return jsonify(msg='Your password has been reset.')
    return jsonify(msg='passwords must match'), 400


@user_account.route('/registration', methods=["POST"])
def registration():
    request_data = request.get_json()
    user = User.create(request_data)
    if not user:
        return jsonify(msg='username is not allowed'), 400
    send_email_confirmation_mail(user, request.headers.get('X-ORIGIN'))
    return jsonify(msg='Проверьте вашу почту и следуйте инструкциям для её подтверждения')


@user_account.route('/confirm_email', methods=['POST'])
def confirm_email():
    request_data = request.get_json()
    user = User.verify_token(request_data.get('token'), 'confirm_email')
    if not user:
        return jsonify(msg='Wrong token'), 400
    user.verify_email()
    return jsonify(msg='Your email has been confirmed.')


@user_account.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(msg='logout successful')
