from flask import request, jsonify, render_template
from flask_login import login_required, current_user

from . import game
from ..api_game.models import GameRoom, get_not_ended_room_by_name, get_room_by_id


@game.route('/create', methods=["POST"])
@login_required
def room_create():
    request_data = request.get_json()
    if get_not_ended_room_by_name(request_data.get('name')):
        return jsonify('Room with this name already exists'), 401

    validation_error = GameRoom.validate_rules(request_data.get('rules'))
    if validation_error:
        return jsonify(validation_error), 401

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

    return jsonify(
        name=room.name,
        id=room.id,
        state='ended' if room.is_ended else 'running' if room.is_running else 'created')


@game.route('/game_data/<room_id>')
@login_required
def get_game_data(room_id):
    """returns json with game_data"""
    room = get_room_by_id(room_id)
    try:
        game_state = room.game_state.state
    except AttributeError:
        game_state = None
    return jsonify(
        turns=room.get_turns(),
        is_ended=room.is_ended,
        winner_name=room.get_winner_name(),
        next_player=game_state.get_current_player().name if game_state and not room.is_ended else None
    )


# todo remove this
@game.route('/room_data/<room_id>')
def get_room_data(room_id):
    """
    returns json with game_data
    used in `.game_core.app` to show game replay
    """
    room = get_room_by_id(room_id)
    return jsonify(
        turns=room.get_turns(),
        spawn_points=room.game_state.state.get_spawn_points(),
        rules=room.rules,
    )


# todo remove this
@game.route('/game_field/<room_id>')
@login_required
def get_game_field(room_id):
    """
    returns json with game_field data. use it only for testing
    used in `.templates.admin_map.html` to show game map
    """
    room = get_room_by_id(room_id)
    if room:
        try:
            return jsonify(room.on_get_field())
        except Exception as e:
            print(e)
            return {'field': 'Error - old engine version'}
    return {'field': 'Error - id'}


@game.route('/players_stats/<room_id>')
@login_required
def get_players_stats(room_id):
    """returns json with players_stats data"""
    room = get_room_by_id(room_id)
    try:
        game_state = room.game_state.state
    except AttributeError:
        game_state = None
    return jsonify(game_state.get_players_data() if game_state else None)


# todo remove this
@game.route('/admin/map')
@login_required
def admin_map():
    """view of `game_map`"""
    return render_template('admin_map.html')
