from flask import render_template, redirect, url_for, request, flash
from flask_login import logout_user, login_required, current_user, login_user

from . import main
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangeNameForm, ChangePwdForm, ResetPasswordRequestForm
from .models import User, get_user_by_name
from ..utils.hider import get_hidden_email, get_hidden_pwd
from ..utils.mail_utils import send_email_confirmation_mail, send_password_reset_email


@main.errorhandler(404)
def handle_404(err):
    """view of `404` page"""
    return render_template('404.html'), 404


@main.route('/')
def index():
    """view of `game` page"""
    return render_template('index.html')


@main.route('/rules')
def rules():
    """view of `rules` page"""
    return render_template('rules.html')


@main.route('/login', methods=["POST", "GET"])
def login():
    """
    view of `login` page
    available methods: POST, GET

    render login form
    logs in user after verification
    """
    if current_user.is_authenticated:
        return redirect(request.args.get("next") or url_for('main.profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_name(form.name.data)
        if user and user.check_password(form.pwd.data):
            rm = form.remember.data
            login_user(user, remember=rm)
            return redirect(request.args.get("next") or url_for('main.profile'))
        flash("Неверная пара логин/пароль", "error")
    return render_template("profile/login.html", form=form)


@main.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = get_user_by_name(form.username.data)
        if user:
            send_password_reset_email(user)
        flash('Проверьте вашу почту и следуйте инструкциям для сброса пароля', 'info')
        return redirect(url_for('main.login'))
    return render_template('profile/reset_password_request.html', form=form)


@main.route('/registration', methods=["POST", "GET"])
def registration():
    """
    view of `registration` page
    available methods: POST, GET
    creates User after validation
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        u = User(form.username.data, form.user_email.data, form.pwd.data)
        flash('Проверьте вашу почту и следуйте инструкциям для её подтверждения', 'info')
        return redirect(url_for('main.login'))
    return render_template('profile/registration.html', form=form)


@main.route('/profile')
@login_required
def profile():
    """view of `profile` page"""
    return render_template('profile/profile.html')


@main.route('/profile_settings')
@login_required
def profile_settings():
    """view of `profile` page"""
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    return render_template('profile/profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           success=False,
                           msg='',
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_email', methods=["POST"])
@login_required
def profile_settings_email():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    success = False
    msg = ''

    if email_form.validate_on_submit():
        current_user.set_email(email_form.new_email.data)
        send_email_confirmation_mail(current_user)
        success = True
        msg = 'email'

    return render_template('profile/profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           success=success,
                           msg=msg,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_name', methods=["POST"])
@login_required
def profile_settings_name():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    success = False
    msg = ''

    if name_form.validate_on_submit():
        current_user.set_name(name_form.new_name.data)
        success = True
        msg = 'name'

    return render_template('profile/profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           success=success,
                           msg=msg,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_pwd', methods=["POST"])
@login_required
def profile_settings_pwd():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    success = False
    msg = ''

    if pwd_form.validate_on_submit():
        current_user.set_pwd(pwd_form.new_pwd.data)
        success = True
        msg = 'pwd'

    return render_template('profile/profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           success=success,
                           msg=msg,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/confirm_email/<token>', methods=['GET', 'POST'])
@login_required
def confirm_email(token):
    user = User.verify_token(token, 'confirm_email')
    if not user:
        return redirect(url_for('main.index'))
    user.verify_email()
    return render_template('profile/email_confirmed.html')


@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_token(token, 'reset_password')
    if not user:
        return redirect(url_for('index'))
    form = ChangePwdForm()
    if form.validate_on_submit():
        user.set_pwd(form.new_pwd.data)
        flash('Your password has been reset.', 'info')
        return redirect(url_for('main.login'))
    return render_template('profile/reset_password.html', form=form)


@main.route("/logout")
@login_required
def logout():
    """
    view of `logout` page
    logs out user
    """
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/play')
@login_required
def play():
    """view of `play` page"""
    return render_template('play.html')
