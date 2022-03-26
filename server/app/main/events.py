from flask_login import current_user
from flask_socketio import send, emit, join_room, leave_room

from .models import GameRoom
from .. import sio


@sio.on('join', namespace='/game_room')
def on_connect(data: dict):
    room_name = data.get('room')
    print(f'user {current_user.user_name} joins the room {room_name}')
    join_room(room_name)
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    rules = room.rules
    players_name = [user.user_name for user in room.players]
    players_amount = rules.get('players_amount')
    emit(
        'join',
        {
            "players": players_name,
            "players_amount": players_amount,
            "bots_amount": rules.get('bots_amount'),
            "creator": room.creator.user_name,
            "is_ready": True if len(players_name) == players_amount else False,
        },
        room=room_name
    )


@sio.on('disconnect', namespace='/game_room')
def handle_disconnect():
    print('disconnected')


@sio.on('leave', namespace='/game_room')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)


@sio.on('start', namespace='/game_room')
def on_start(data):
    print('start')
    room = data['room']
    emit('start', room=room)
