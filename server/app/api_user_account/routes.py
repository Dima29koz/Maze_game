import os

from flask import request, jsonify, send_file
from flask_login import login_user, login_required, current_user, logout_user

from . import user_account
from .. import login_manager
from ..api_game.models import get_user_won_games_amount
from .models import get_user_by_name, User, get_user_by_id
from ..utils.hider import get_hidden_email
from ..utils.mail_utils import send_password_reset_email, send_email_confirmation_mail


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify('login required'), 401


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


@user_account.route('/edit_profile/email', methods=['POST'])
@login_required
def edit_email():
    request_data = request.get_json()
    current_user.set_email(request_data.get('email'))

    send_email_confirmation_mail(current_user, request.headers.get('X-ORIGIN'))
    return jsonify(
        id=current_user.id,
        username=current_user.user_name,
        email=get_hidden_email(current_user.user_email),
        is_email_verified=current_user.is_email_verified,
    )


@user_account.route('/edit_profile/password', methods=['POST'])
@login_required
def edit_password():
    request_data = request.get_json()

    if not current_user.check_password(request_data.get('current_pwd')):
        return jsonify(msg='Wrong username or password'), 401

    new_pwd = request_data.get('pwd')
    new_pwd_repeat = request_data.get('pwd_repeat')
    if new_pwd == new_pwd_repeat:
        current_user.set_pwd(new_pwd)

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
    if request_data.get('pwd') != request_data.get('pwd_repeat'):
        return jsonify(msg='passwords must match'), 400
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


@user_account.route('/user_games')
@login_required
def get_user_games():
    user_games = current_user.games
    return jsonify({
        'games_won': get_user_won_games_amount(current_user.id),
        'games_total': len(user_games),  # todo remove running games from result
        'games': [{
            'id': game.id,
            'name': game.name,
            'status': 'ended' if game.is_ended else 'running' if game.is_running else 'created',
            'winner': game.get_winner_name(),
            'details': 'details',
        } for game in user_games]
    })


@user_account.route('/img/<user_name>')
@login_required
def get_user_avatar(user_name):
    """API for getting user ave image"""
    filename = 'default_avatar.jpg'
    file_path = os.path.join(os.path.split(user_account.root_path)[0], 'static', 'images', filename)
    return send_file(file_path, mimetype='image/jpg')
