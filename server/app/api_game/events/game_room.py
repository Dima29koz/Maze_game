from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, Namespace, ConnectionRefusedError

from server.app.api_game.models import get_room_by_id, GameRoom


class GameRoomNamespace(Namespace):
    """Handle events on game_room page"""

    @staticmethod
    def on_connect(auth: dict | None):
        """
        added user to room;
        emits `join`, `get_spawn`
        """
        if not auth:
            raise ConnectionRefusedError('unauthorized!')
        room = GameRoom.verify_token(auth.get('token', ''), current_user)
        if not room or room.is_ended or room.is_running:
            raise ConnectionRefusedError('unauthorized!')

        session['room_id'] = room.id
        join_room(room.id)

        emit('join', {
            'room_name': room.name,
            'room_info': room.get_info()
        }, room=room.id)
        emit('get_spawn', {
            'field': room.game_state.state.get_field_pattern_list(),
            'spawn_info': room.game_state.state.get_spawn_point(current_user.user_name)
        })

    @staticmethod
    def on_set_spawn(data: dict):
        """
        added spawned player to game;
        emits `set_spawn`
        """
        room_id = session.get('room_id')
        room = get_room_by_id(room_id)
        turn = room.players.index(current_user) + 1
        if room.game_state.state.field.spawn_player(data.get('spawn'), current_user.user_name, turn):
            room.save()
            emit('join', {
                'room_name': room.name,
                'room_info': room.get_info()
            }, room=room_id)

    @staticmethod
    def on_leave():
        """User leaves a room"""
        room_id = session.get('room_id')
        leave_room(room_id)
        room = get_room_by_id(room_id)
        if room.remove_player(current_user):
            emit('join', {
                'room_name': room.name,
                'room_info': room.get_info()
            }, room=room_id)

    @staticmethod
    def on_disconnect():
        """User disconnect from a room"""
        # room_id = session.pop('room_id', '')
        # leave_room(room_id)
        pass
        # room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        # emit('join', room.on_join(), room=room_name)

    @staticmethod
    def on_start():
        """
        starting Game
        emits `start`
        """
        room_id = session.get('room_id')
        room = get_room_by_id(room_id)

        if room.creator != current_user:
            emit('error', {'type': 'start', 'msg': 'only creator allowed to start game'})
            return
        if not room.is_ready_to_start():
            emit('error', {'type': 'start', 'msg': 'all players should join and select spawn'})
            return

        room.on_start()
        emit('start', room=room_id)
