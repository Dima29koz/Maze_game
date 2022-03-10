from flask_socketio import send

from .. import sio


@sio.on('my_event', namespace='/game_room')
def handle_my_event(data):
    print('received message: ' + data)
    send(data)


@sio.on('message', namespace='/game_room')
def handle_message(data):
    print('received message: ' + data)
    send(data)


@sio.on('connect', namespace='/game_room')
def handle_connect(data):
    print('connected', data)


@sio.on('disconnect', namespace='/game_room')
def handle_disconnect():
    print('disconnected')
