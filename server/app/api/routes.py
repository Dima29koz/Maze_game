from flask import jsonify
from flask_login import login_required, current_user

from . import api
from ..main.models import GameRoom, get_not_ended_room_by_name, get_room_by_id


@api.route('/api/game_data/<room_id>')
@login_required
def get_game_data(room_id):
    """returns json with game_data"""
    room = get_room_by_id(room_id)
    return jsonify(
        turns=room.get_turns(),
        is_ended=room.is_ended,
        next_player=room.game.get_current_player().name
    )


@api.route('/api/players_stat/<room_id>')
@login_required
def get_players_stat(room_id):
    """returns json with players_stat data"""
    room = get_room_by_id(room_id)
    return jsonify(room.game.get_players_data())


@api.route('/api/game_field/<room_id>')
@login_required
def get_game_field(room_id):
    """returns json with game_field data. use it only for testing"""
    room = get_room_by_id(room_id)
    return jsonify(room.on_get_field())


@api.route('/api/user_games')
@login_required
def get_user_games():
    """returns json with user games data."""
    user_games = current_user.games
    return jsonify({
        'games_won': GameRoom.query.filter_by(winner_id=current_user.id).count(),
        'games_total': len(user_games),  # todo remove running games from result
        'games': [{
            'id': game.id,
            'name': game.name,
            'status': 'ended' if game.is_ended else 'running' if game.is_running else 'created',
            'winner': game.winner.user_name if game.is_ended else '-',
            'details': 'details',
            } for game in user_games]
        }
    )
