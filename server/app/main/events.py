from flask_login import current_user
from flask_socketio import send, emit, join_room, leave_room

from .models import GameRoom, TurnInfo
from .. import sio


@sio.on('join', namespace='/game_room')
def on_connect(data: dict):
    room_name = data.get('room')
    join_room(room_name)
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    rules = room.rules
    players_name = [user.user_name for user in room.players]
    players_amount = rules.get('players_amount')
    players_bots = rules.get('bots_amount') + players_amount
    ready_cond = len(players_name) == players_amount and len(room.game.field.players) == players_bots
    emit(
        'join',
        {
            "players": players_name,
            "players_amount": players_amount,
            "bots_amount": rules.get('bots_amount'),
            "bots_name": rules.get('bots'),
            "creator": room.creator.user_name,
            "is_ready": ready_cond,
        },
        room=room_name
    )
    emit('get_spawn', {'field': room.game.field.get_field_pattern_list()})


@sio.on('set_spawn', namespace='/game_room')
def on_set_spawn(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
    turn = room.players.index(current_user) + 1
    if room.game.field.spawn_player(data.get('spawn'), current_user.user_name, turn):
        room.save()
        rules = room.rules
        pl_amount = len(room.players) == rules.get('players_amount')
        spawned_pl_amount = len(room.game.field.players) == rules.get('bots_amount') + rules.get('players_amount')
        emit('set_spawn',
             {
                 'creator': room.creator.user_name,
                 'is_ready': pl_amount and spawned_pl_amount
             },
             room=room_name)


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
    room.start()
    response = []
    for player in room.game.field.players:
        resp, next_player = room.game.make_turn(player.name, 'info')
        response.append(resp)
    room.save()
    for resp in response:
        turn_info_dict = resp.get_turn_info()
        turn_info = TurnInfo(game_room_id=room.id, player_name=turn_info_dict.get('player_name'))
        turn_info.add_turn(turn_info_dict, resp.get_info())

    emit('start', room=room_name)


@sio.on('join', namespace='/game')
def on_connect_game(data):
    room_name = data.get('room')
    join_room(room_name)
    emit('join', {'current_user': current_user.user_name})


@sio.on('action', namespace='/game')
def on_action(data):
    room_name = data.get('room')
    room: GameRoom = GameRoom.query.filter_by(name=room_name).first()

    next_player = turn_handler(room, room_name, current_user.user_name, data.get('action'), data.get('direction'))
    while next_player.is_bot:
        next_player = turn_handler(room, room_name, next_player.name, 'skip')


def turn_handler(room: GameRoom, room_name: str, player_name: str, action: str, direction: str | None = None):
    turn_resp, next_player = room.game.make_turn(
        player_name, action, direction)
    room.game.check_win_condition(room.rules)
    room.save()
    if turn_resp:
        turn_info_dict = turn_resp.get_turn_info()
        turn_info = TurnInfo(game_room_id=room.id, player_name=turn_info_dict.get('player_name'))
        turn_info.add_turn(turn_info_dict, turn_resp.get_info())
        emit('turn_info',
             {
                 'player': turn_info.player_name,
                 'action': turn_info.action,
                 'direction': turn_info.direction,
                 'response': turn_info.turn_response,
                 'next_player_name': next_player.name,
                 'turns_end_resp': f'{player_name} wins' if not room.game.is_running else '',
                 'field': room.game.field.get_field_list(),
             },
             room=room_name)
    return next_player


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
