from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, Namespace

from server.app.main.models import GameRoom


class GameRoomNamespace(Namespace):
    """Handle events on game_room page"""
    def on_join(self, data: dict):
        """
        added user to room;
        emits `join`, `get_spawn`
        """
        room_name = data.get('room')
        join_room(room_name)
        session['room'] = room_name
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        emit('join', room.on_join(), room=room_name)
        emit('get_spawn', {'field': room.game.field.get_field_pattern_list(),
                           'spawn_info': room.game.get_spawn_point(current_user.user_name)})

    def on_set_spawn(self, data: dict):
        """
        added spawned player to game;
        emits `set_spawn`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        turn = room.players.index(current_user) + 1
        if room.game.field.spawn_player(data.get('spawn'), current_user.user_name, turn):
            room.save()
            emit('join', room.on_join(), room=room_name)

    def on_leave(self, data: dict):
        """User leaves a room"""
        room_name = data.get('room')
        leave_room(room_name)
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        room.remove_player(current_user.user_name)
        emit('join', room.on_join(), room=room_name)

    def on_disconnect(self):
        """User disconnect from a room"""
        room_name = session.get('room', '')
        leave_room(room_name)
        # room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        # emit('join', room.on_join(), room=room_name)

    def on_start(self, data: dict):
        """
        starting Game
        emits `start`
        """
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        room.on_start()
        emit('start', room=room_name)
