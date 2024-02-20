from flask import session
from flask_login import current_user
from flask_socketio import Namespace, join_room, emit

from server.app.game.models import get_room_by_id


class GameNamespace(Namespace):
    """Handle events on game page"""

    @staticmethod
    def on_join(data: dict):
        """
        added user to socketIO room;
        emits `join`
        """
        room_id = data.get('room_id')
        session['room_id'] = room_id
        join_room(room_id)
        room = get_room_by_id(room_id)
        emit('join', {'current_user': current_user.user_name, 'rules': room.rules})

    @staticmethod
    def on_action(data: dict):
        """
        handle player`s turn;
        emits `turn_info`, `win_msg`
        """
        room_id = data.get('room_id')
        room = get_room_by_id(room_id)

        current_player = room.game_state.state.get_current_player()
        if current_player.name != current_user.user_name:  # todo bugs if there is bot with same name in room
            return

        if room.bot_state:
            room.bot_state.state.turn_prepare(current_player.name,
                                              room.game_state.state.get_allowed_abilities(current_player))
        next_player, turn_data, win_data = room.on_turn(
            current_player, data.get('action'), data.get('direction'))
        if turn_data:
            emit('turn_info',
                 {
                     'turn_data': turn_data,
                     'players_stat': room.game_state.state.get_players_data(),
                 },
                 room=room_id)
        if win_data:
            emit('win_msg', win_data, room=room_id)
        while next_player.is_bot and not win_data:
            action, direction = room.bot_state.state.make_decision(
                next_player.name, room.game_state.state.get_allowed_abilities(next_player))
            next_player, turn_data, win_data = room.on_turn(
                next_player, action.name, direction.name if direction else None)
            if turn_data:
                emit('turn_info',
                     {
                         'turn_data': turn_data,
                         'players_stat': room.game_state.state.get_players_data(),
                     },
                     room=room_id)
            if win_data:
                emit('win_msg', win_data, room=room_id)

    @staticmethod
    def on_get_allowed_abilities(data: dict):
        """
        emits `set_allowed_abilities` with data[is_active, allowed_abilities]
        """
        room_id = data.get('room_id')
        room = get_room_by_id(room_id)
        active_player = room.game_state.state.get_current_player()
        emit('set_allowed_abilities',
             {
                 'is_active': current_user.user_name == active_player.name,
                 'next_player_name': active_player.name,
                 'allowed_abilities': room.game_state.state.get_allowed_abilities_str(active_player),
             })

    @staticmethod
    def on_disconnect():
        """User disconnect from a game"""
        # room_id = session.pop('room_id')
        # leave_room(room_id)
        pass
