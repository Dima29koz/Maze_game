from flask_login import current_user
from flask_socketio import send, emit, join_room, leave_room, Namespace

from server.app.main.models import GameRoom


class GameRoomNamespace(Namespace):
    def on_join(self, data: dict):
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

    def on_set_spawn(self, data):
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

    def on_disconnect(self):
        print('disconnected')

    def on_leave(self, data):
        """User leaves a room"""

        username = data['username']
        room = data['room']
        leave_room(room)
        send({"msg": username + " has left the room"}, room=room)

    def on_start(self, data):
        room_name = data.get('room')
        room: GameRoom = GameRoom.query.filter_by(name=room_name).first()
        room.start()
        for player in room.game.field.players:
            room.on_turn(player.name, 'info')

        emit('start', room=room_name)



