from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, Namespace

from server.app.main.models import get_room_by_id


class GameRoomNamespace(Namespace):
    """Handle events on game_room page"""
    def on_join(self, data: dict):
        """
        added user to room;
        emits `join`, `get_spawn`
        """
        room_id = data.get('room_id')
        session['room_id'] = room_id
        join_room(room_id)
        room = get_room_by_id(room_id)
        emit('join', room.get_info(), room=room_id)
        emit('get_spawn', {'field': room.game.field.get_field_pattern_list(),
                           'spawn_info': room.game.get_spawn_point(current_user.user_name)})

    def on_set_spawn(self, data: dict):
        """
        added spawned player to game;
        emits `set_spawn`
        """
        room_id = session.get('room_id', '')
        room = get_room_by_id(room_id)
        turn = room.players.index(current_user) + 1
        if room.game.field.spawn_player(data.get('spawn'), current_user.user_name, turn):
            room.save()
            emit('join', room.get_info(), room=room_id)

    def on_leave(self):
        """User leaves a room"""
        room_id = session.pop('room_id', '')
        leave_room(room_id)
        room = get_room_by_id(room_id)
        if room.remove_player(current_user):
            emit('join', room.get_info(), room=room_id)

    def on_disconnect(self):
        """User disconnect from a room"""
        room_id = session.pop('room_id', '')
        leave_room(room_id)
        # room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        # emit('join', room.on_join(), room=room_name)

    def on_start(self):
        """
        starting Game
        emits `start`
        """
        room_id = session.get('room_id', '')
        room = get_room_by_id(room_id)
        room.on_start()
        emit('start', room=room_id)
