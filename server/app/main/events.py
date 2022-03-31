from flask_login import current_user
from flask_socketio import send, emit, join_room, leave_room

from .models import GameRoom, TurnInfo
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
            "bots_name": rules.get('bots'),
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
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    room.add_game()
    emit('start', room=room_name)


@sio.on('join', namespace='/game')
def on_connect_game(data):
    room_name = data.get('room')
    join_room(room_name)
    print(current_user.user_name, "connected to room", room_name)
    emit('join', {'current_user': current_user.user_name})


@sio.on('action', namespace='/game')
def on_action(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    resp = room.game.make_turn(
        current_user.user_name, data.get('action'), data.get('direction'))

    room.save(room.game)
    if resp:
        for turn_resp, next_player_name in resp:
            turn_info_dict = turn_resp.get_turn_info()
            turn_info = TurnInfo(game_room_id=room.id, player_name=turn_info_dict.get('player_name'))
            turn_info.add_turn(turn_info_dict, turn_resp.get_info())

            emit('turn_info',
                 {
                     'player': turn_info.player_name,
                     'action': turn_info.action,
                     'direction': turn_info.direction,
                     'response': turn_info.turn_response,
                     'next_player_name': next_player_name,
                 },
                 room=room_name)


@sio.on('check_active', namespace='/game')
def on_check_active(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    active_player = room.game.get_current_player()
    emit('set_active',
         {
             'is_active': True if current_user.user_name == active_player.name else False,
             'allowed_abilities': room.game.get_allowed_abilities_str(active_player),
         })


@sio.on('get_history', namespace='/game')
def on_get_history(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    turns: list[TurnInfo] = room.turn_info
    emit('set_history',
         {
             'turns': [turn.to_dict() for turn in turns],
         })


@sio.on('get_players_stat', namespace='/game')
def on_get_players_stat(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    emit('set_players_stat',
         {
             'players_data': room.game.get_players_data(),
         },
         room=room_name)
