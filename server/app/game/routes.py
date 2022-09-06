from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user

from . import game
from .forms import RulesForm, LoginRoomForm
from .models import GameRoom, get_not_ended_room_by_name


@game.route('/join', methods=["POST", "GET"])
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
                return redirect(url_for("game.game_page", room=room.name, room_id=room.id))
            return redirect(url_for("game.game_room", room=room.name, room_id=room.id))
        flash("Комната полностью заполнена", "error")

    return render_template('join.html', form=form)


@game.route('/create', methods=["POST", "GET"])
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
        return redirect(url_for("game.game_room", room=room.name, room_id=room.id))
    return render_template('create.html', form=form)


@game.route('/game_room')
@login_required
def game_room():
    """view of `game_room` page"""
    return render_template('game_room.html')


@game.route('/game')
@login_required
def game_page():
    """view of `game` page"""
    return render_template('game.html')


@game.route('/admin/map')
@login_required
def admin_map():
    """view of `game_map`"""
    return render_template('admin_map.html')
