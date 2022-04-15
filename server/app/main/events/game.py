from flask_login import current_user
from flask_socketio import Namespace, join_room, emit

from server.app.main.models import GameRoom


class GameNamespace(Namespace):
    """Handle events on game page"""

    def on_join(self, data: dict):
        """
        added user to room;
        emits `join`
        """
        room_name = data.get('room')
        join_room(room_name)
        emit('join', {'current_user': current_user.user_name})

    def on_action(self, data: dict):
        """
        calculates player turn;
        emits `turn_info`, `sys_msg`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        next_player, turn_data, win_data = room.on_turn(
            current_user.user_name, data.get('action'), data.get('direction'))
        if turn_data:
            emit('turn_info', turn_data, room=room_name)
        if win_data:
            emit('sys_msg', win_data, room=room_name)
        while next_player.is_bot and not win_data:
            next_player, response, win_data = room.on_turn(next_player.name, 'skip')
            if response:
                emit('turn_info', response, room=room_name)
            if win_data:
                emit('sys_msg', win_data, room=room_name)

    def on_check_active(self, data: dict):
        """
        check users allowed abilities;
        emits `set_active`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        active_player = room.game.get_current_player()
        emit('set_active',
             {
                 'is_ended': room.is_ended,
                 'is_active': True if current_user.user_name == active_player.name else False,
                 'allowed_abilities': room.game.get_allowed_abilities_str(active_player),
             })

    def on_get_history(self, data: dict):
        """
        loads game turns from db;
        emits `set_history`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        emit('set_history',
             {
                 'turns': room.get_turns(),
             })

    def on_get_players_stat(self, data: dict):
        """
        loads players stat;
        emits `set_players_stat`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        emit('set_players_stat',
             {
                 'players_data': room.game.get_players_data(),
             },
             room=room_name)
