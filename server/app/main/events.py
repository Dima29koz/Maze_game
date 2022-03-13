from flask_socketio import send, emit, join_room, leave_room

from .. import sio, game_rooms


@sio.on('my_event', namespace='/game_room')
def handle_my_event(data):
    print('received message: ', data)
    send(data)


@sio.on('message', namespace='/game_room')
def handle_message(data):
    print('received message: ', data.get('data'))

    # emit('message', data.get('data'))
    emit('message', {'data' : game_rooms[0].make_turn()})


@sio.on('connect', namespace='/game_room')
def handle_connect():
    print('connected')


@sio.on('disconnect', namespace='/game_room')
def handle_disconnect():
    print('disconnected')


@sio.on('join', namespace='/game_room')
def on_join(data):
    """User joins a room"""
    print('join')
    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that new user has joined
    send({"data": username + " has joined the " + room + " room."}, room=room)


@sio.on('leave', namespace='/game_room')
def on_leave(data):
    """User leaves a room"""

    username = data['username']
    room = data['room']
    leave_room(room)
    send({"msg": username + " has left the room"}, room=room)