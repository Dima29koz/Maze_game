from flask import jsonify
from flask_login import login_required

from . import api
from ..main.models import GameRoom


@api.route('/api/game_data/<room_name>')
@login_required
def get_game_data(room_name):
    """returns json with game_data"""
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    return jsonify(
        turns=room.get_turns(),
        is_ended=room.is_ended,
        next_player=room.game.get_current_player().name
    )


@api.route('/api/players_stat/<room_name>')
@login_required
def get_players_stat(room_name):
    """returns json with players_stat data"""
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    return jsonify(room.game.get_players_data())


@api.route('/api/game_field/<room_name>')
@login_required
def get_game_field(room_name):
    """returns json with game_field data. use it only for testing"""
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    return jsonify(room.on_get_field())
