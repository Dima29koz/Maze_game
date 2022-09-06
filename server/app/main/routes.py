from flask import render_template, redirect, url_for, request, flash
from flask_login import logout_user, login_required, current_user, login_user

from . import main
from .forms import LoginForm, RegistrationForm
from .models import User, get_user_by_name


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
        u = User(form.username.data, form.pwd.data)
        print(u.user_name, 'added', 'redirecting. . .')
        return redirect(url_for('main.login'))
    return render_template('registration.html', form=form)


@main.route('/profile')
@login_required
def profile():
    """view of `profile` page"""
    return render_template('profile.html')


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
