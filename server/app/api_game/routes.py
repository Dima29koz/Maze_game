from flask import request, jsonify
from flask_login import login_required, current_user

from . import game
from ..game.models import GameRoom, get_not_ended_room_by_name


@game.route('/create', methods=["POST"])
@login_required
def room_create():
    request_data = request.get_json()
    if get_not_ended_room_by_name(request_data.get('name')):
        return jsonify('Room with this name already exists'), 401

    room = GameRoom.create(
        request_data.get('name'),
        request_data.get('pwd'),
        request_data.get('rules'),
        current_user)
    return jsonify(name=room.name, id=room.id)


@game.route('/join', methods=["POST"])
@login_required
def room_join():
    request_data = request.get_json()
    room = get_not_ended_room_by_name(request_data.get('name'))
    if not room or not room.check_password(request_data.get('pwd')):
        return jsonify(msg='Wrong room name or password'), 401

    if not room.add_player(current_user):
        return jsonify(msg='There are no empty slots in the room'), 401

    return jsonify(name=room.name, id=room.id)
