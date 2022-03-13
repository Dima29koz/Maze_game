from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from flask_login import login_user, login_required, logout_user, current_user

from . import main
from .forms import RegistrationForm, LoginForm, RulesForm
from .models import User

from .. import game_rooms
from ..utils.game import Game


@main.errorhandler(404)
def handle_404(err):
    return render_template('404.html'), 404


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/play')
@login_required
def play():
    return render_template('play.html')


@main.route('/rules')
def rules():
    return render_template('rules.html')


@main.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(request.args.get("next") or url_for("main.profile"))

    form = LoginForm()
    if form.validate_on_submit():
        user: User | None = User.query.filter_by(user_name=form.name.data).first()
        if user and user.check_password(form.pwd.data):
            rm = form.remember.data
            login_user(user, remember=rm)
            return redirect(request.args.get("next") or url_for("main.profile"))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", form=form)


@main.route('/registration', methods=["POST", "GET"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(user_name=form.username.data)
        user.set_pwd(form.pwd.data)
        user.add()
        return redirect(url_for('main.login'))
    return render_template('registration.html', form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@main.route('/join')
@login_required
def room_join():
    return render_template('join.html')


@main.route('/game_room')
@login_required
def game_room():
    return render_template('game_room.html', user_name=current_user.user_name)


@main.route('/create', methods=["POST", "GET"])
@login_required
def room_create():
    form = RulesForm()
    if form.validate_on_submit():
        game = Game()
        game.create()
        game_rooms.append(game)
        return redirect(url_for("main.game_room"))
    return render_template('create.html', form=form)
