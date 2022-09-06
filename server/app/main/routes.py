from flask import render_template, redirect, url_for, request, flash
from flask_login import logout_user, login_required, current_user, login_user

from . import main
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangeNameForm, ChangePwdForm
from .models import User, get_user_by_name
from ..utils.hider import get_hidden_email, get_hidden_pwd


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
    return render_template("login.html", form=form)


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
        return redirect(url_for('main.login'))
    return render_template('registration.html', form=form)


@main.route('/profile')
@login_required
def profile():
    """view of `profile` page"""
    return render_template('profile.html')


@main.route('/profile_settings')
@login_required
def profile_settings():
    """view of `profile` page"""
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    return render_template('profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_email', methods=["POST"])
@login_required
def profile_settings_email():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()
    if email_form.validate_on_submit():
        current_user.set_email(email_form.new_email.data)

    return render_template('profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_name', methods=["POST"])
@login_required
def profile_settings_name():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()

    if name_form.validate_on_submit():
        current_user.set_name(name_form.new_name.data)

    return render_template('profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


@main.route('/profile_setting_pwd', methods=["POST"])
@login_required
def profile_settings_pwd():
    email_form = ChangeEmailForm()
    name_form = ChangeNameForm()
    pwd_form = ChangePwdForm()

    if pwd_form.validate_on_submit():
        current_user.set_pwd(pwd_form.new_pwd.data)
    return render_template('profile_settings.html',
                           cur_email=get_hidden_email(current_user.user_email),
                           cur_pwd=get_hidden_pwd(),
                           cur_name=current_user.user_name,
                           email_form=email_form,
                           name_form=name_form,
                           pwd_form=pwd_form)


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
