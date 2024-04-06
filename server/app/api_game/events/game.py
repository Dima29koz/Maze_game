from flask import session
from flask_login import current_user
from flask_socketio import Namespace, join_room, emit, ConnectionRefusedError

from server.app.api_game.models import get_room_by_id, GameRoom


class GameNamespace(Namespace):
    """Handle events on game page"""

    @staticmethod
    def on_connect(auth: dict | None):
        """
        added user to socketIO room;
        emits `join`
        """
        if not auth:
            raise ConnectionRefusedError('unauthorized!')
        room = GameRoom.verify_token(auth.get('token', ''), current_user)
        if not room or (not room.is_running and not room.is_ended):
            raise ConnectionRefusedError('unauthorized!')

        session['room_id'] = room.id
        join_room(room.id)
        emit('join', {
            'room_name': room.name,
            'rules': room.rules,
            'game_data': dict(
                error='old engine version' if not room.game else None,
                turns=room.get_turns(),
                is_ended=room.is_ended,
                winner_name=room.get_winner_name(),
                next_player=room.next_player_name,
                players_stats=room.players_stats
            )
        })

    @staticmethod
    def on_action(data: dict):
        """
        handle player`s turn;
        emits `turn_info`
        """
        room_id = session.get('room_id')
        room = get_room_by_id(room_id)

        current_player = room.game_state.state.get_current_player()
        if current_player.name != current_user.user_name:  # todo bugs if there is bot with same name in room
            return

        if room.bot_state:
            room.bot_state.state.turn_prepare(current_player.name,
                                              room.game_state.state.get_allowed_abilities(current_player))
        next_player, turn_data, winner_name = room.on_turn(
            current_player, data.get('action'), data.get('direction'))
        if turn_data:
            emit('turn_info',
                 {
                     'turn_data': turn_data,
                     'players_stats': room.players_stats,
                     'next_player': next_player.name if not winner_name else None,
                     'winner_name': winner_name
                 },
                 room=room_id)

        while next_player.is_bot and not winner_name:
            action, direction = room.bot_state.state.make_decision(
                next_player.name, room.game_state.state.get_allowed_abilities(next_player))
            next_player, turn_data, winner_name = room.on_turn(
                next_player, action.name, direction.name if direction else None)
            if turn_data:
                emit('turn_info',
                     {
                         'turn_data': turn_data,
                         'players_stats': room.players_stats,
                         'next_player': next_player.name if not winner_name else None,
                         'winner_name': winner_name
                     },
                     room=room_id)

    @staticmethod
    def on_get_allowed_abilities():
        """
        emits `set_allowed_abilities` with data[is_active, allowed_abilities]
        """
        room_id = session.get('room_id')
        room = get_room_by_id(room_id)
        emit('set_allowed_abilities',
             {
                 'is_active': current_user.user_name == room.next_player_name,
                 'next_player_name': room.next_player_name,
                 'allowed_abilities': room.current_player_allowed_abilities,
             })

    @staticmethod
    def on_disconnect():
        """User disconnect from a game"""
        # room_id = session.pop('room_id')
        # leave_room(room_id)
        pass
