from functools import partial
from browser import window, alert

io = window.io
socket = io('/game_room')


def on_connect():
    window.console.log('connect')
    socket.emit('message', {'data': 'wow connected!'})


def on_message(data):
    window.console.log(data)


socket.on('connect', on_connect)
socket.on('message', on_message)
