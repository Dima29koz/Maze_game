from flask_socketio import send, emit, join_room, leave_room

from .models import GameRoom
from .. import sio


@sio.on('my_event', namespace='/game_room')
def handle_my_event(data):
    print('received message: ', data)
    send(data)


@sio.on('message', namespace='/game_room')
def handle_message(data):
    print('received message: ', data.get('data'))

    # emit('message', data.get('data'))
    emit('message', {'data': 'some data'})


@sio.on('connect', namespace='/game_room')
def handle_connect():
    print('connected')


@sio.on('disconnect', namespace='/game_room')
def handle_disconnect():
    print('disconnected')


@sio.on('join', namespace='/game_room')
def on_join(data):
    """User joins a room"""
    username = data["username"]
    room_name = data["room"]
    print(f'user {username} joins the room {room_name}')
    join_room(room_name)
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    players_name = [user.user_name for user in room.players]
    # Broadcast that new user has joined
    emit(
        'join',
        {"players": players_name, "max_players": room.rules.get('players_amount')},
        room=room_name
    )


@sio.on('leave', namespace='/game_room')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)