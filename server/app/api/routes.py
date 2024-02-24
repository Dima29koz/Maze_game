import os

from flask import jsonify, send_file
from flask_login import login_required, current_user

from . import api
from ..game.models import get_room_by_id, get_user_won_games_amount


@api.route('/api/game_data/<room_id>')
@login_required
def get_game_data(room_id):
    """returns json with game_data"""
    room = get_room_by_id(room_id)
    try:
        game = room.game_state.state
    except AttributeError:
        game = None
    return jsonify(
        turns=room.get_turns(),
        is_ended=room.is_ended,
        winner_name=room.get_winner_name(),
        next_player=game.get_current_player().name if game and not room.is_ended else None
    )


@api.route('/api/room_data/<room_id>')
def get_room_data(room_id):
    """returns json with game_data"""
    room = get_room_by_id(room_id)
    return jsonify(
        turns=room.get_turns(),
        spawn_points=room.game_state.state.get_spawn_points(),
        rules=room.rules,
    )


@api.route('/api/players_stat/<room_id>')
@login_required
def get_players_stat(room_id):
    """returns json with players_stat data"""
    room = get_room_by_id(room_id)
    try:
        game = room.game_state.state
    except AttributeError:
        game = None
    return jsonify(game.get_players_data() if game else None)


@api.route('/api/game_field/<room_id>')
@login_required
def get_game_field(room_id):
    """returns json with game_field data. use it only for testing"""
    room = get_room_by_id(room_id)
    if room:
        try:
            return jsonify(room.on_get_field())
        except Exception as e:
            print(e)
            return {'field': 'Error - old engine version'}
    return {'field': 'Error - id'}


@api.route('/api/user_games')
@login_required
def get_user_games():
    """returns json with user games data."""
    user_games = current_user.games
    return jsonify({
        'games_won': get_user_won_games_amount(current_user.id),
        'games_total': len(user_games),  # todo remove running games from result
        'games': [{
            'id': game.id,
            'name': game.name,
            'status': 'ended' if game.is_ended else 'running' if game.is_running else 'created',
            'winner': game.winner.user_name if game.is_ended and game.winner_id else 'Bot'
            if game.is_ended and not game.winner_id else '-',
            'details': 'details',
        } for game in user_games]
    }
    )


@api.route('/api/img/<user_name>')
@login_required
def get_user_avatar(user_name):
    """API for getting user ave image"""
    filename = 'default_avatar.jpg'
    file_path = os.path.join(os.path.split(api.root_path)[0], 'static', 'images', filename)
    return send_file(file_path, mimetype='image/jpg')
