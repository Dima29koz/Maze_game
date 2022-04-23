from flask_login import current_user
from flask_socketio import Namespace, join_room, emit

from server.app.main.models import GameRoom


class GameNamespace(Namespace):
    """Handle events on game page"""

    def on_join(self, data: dict):
        """
        added user to socketIO room;
        emits `join`
        """
        room_name = data.get('room')
        join_room(room_name)
        emit('join', {'current_user': current_user.user_name})

    def on_action(self, data: dict):
        """
        handle player`s turn;
        emits `turn_info`, `win_msg`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        next_player, turn_data, win_data = room.on_turn(
            current_user.user_name, data.get('action'), data.get('direction'))
        if turn_data:
            emit('turn_info',
                 {
                     'turn_data': turn_data,
                     'players_stat': room.game.get_players_data(),
                 },
                 room=room_name)
        if win_data:
            emit('win_msg', win_data, room=room_name)
        while next_player.is_bot and not win_data:
            next_player, turn_data, win_data = room.on_turn(next_player.name, 'skip')
            if turn_data:
                emit('turn_info',
                     {
                         'turn_data': turn_data,
                         'players_stat': room.game.get_players_data(),
                     },
                     room=room_name)
            if win_data:
                emit('sys_msg', win_data, room=room_name)

    def on_get_allowed_abilities(self, data: dict):
        """
        emits `set_allowed_abilities` with data[is_active, allowed_abilities]
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        active_player = room.game.get_current_player()
        emit('set_allowed_abilities',
             {
                 'is_active': current_user.user_name == active_player.name,
                 'allowed_abilities': room.game.get_allowed_abilities_str(active_player),
             })
