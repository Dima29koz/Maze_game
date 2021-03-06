from flask import render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user

from . import main
from .forms import RegistrationForm, LoginForm, RulesForm, LoginRoomForm
from .models import User, GameRoom, get_not_ended_room_by_name, get_user_by_name


@main.errorhandler(404)
def handle_404(err):
    """view of `404` page"""
    return render_template('404.html'), 404


@main.route('/')
def index():
    """view of `main` page"""
    return render_template('index.html')


@main.route('/play')
@login_required
def play():
    """view of `play` page"""
    return render_template('play.html')


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
        return redirect(request.args.get("next") or url_for("main.profile"))

    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_name(form.name.data)
        if user and user.check_password(form.pwd.data):
            rm = form.remember.data
            login_user(user, remember=rm)
            return redirect(request.args.get("next") or url_for("main.profile"))
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


@main.route("/logout")
@login_required
def logout():
    """
    view of `logout` page
    logs out user
    """
    logout_user()
    return redirect(url_for("main.index"))


@main.route('/profile')
@login_required
def profile():
    """view of `profile` page"""
    return render_template('profile.html')


@main.route('/join', methods=["POST", "GET"])
@login_required
def room_join():
    """
    view of `join` page
    available methods: POST, GET
    added player to room
    redirect user into game_room if game is not started
    redirect user into game if is already started
    """
    form = LoginRoomForm()
    if form.validate_on_submit():
        room = get_not_ended_room_by_name(form.name.data)
        if room.add_player(current_user):
            if room.is_running or room.is_ended:
                return redirect(url_for("main.game", room=room.name, room_id=room.id))
            return redirect(url_for("main.game_room", room=room.name, room_id=room.id))
        flash("Комната полностью заполнена", "error")

    return render_template('join.html', form=form)


@main.route('/create', methods=["POST", "GET"])
@login_required
def room_create():
    """
    view of `create` page
    available methods: POST, GET
    create a GameRoom after validation
    redirects to game_room
    """
    form = RulesForm()
    if form.validate_on_submit():
        room = GameRoom(form, current_user)
        return redirect(url_for("main.game_room", room=room.name, room_id=room.id))
    return render_template('create.html', form=form)


@main.route('/game_room')
@login_required
def game_room():
    """view of `game_room` page"""
    return render_template('game_room.html')


@main.route('/game')
@login_required
def game():
    """view of `game` page"""
    return render_template('game.html')


@main.route('/admin/map')
@login_required
def admin_map():
    """view of `game_map`"""
    return render_template('admin_map.html')
