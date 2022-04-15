from copy import copy
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db, login_manager

from GameEngine.game import Game
from GameEngine.rules import rules as default_rules


login_manager.login_view = 'main.login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


user_room = db.Table(
    'user_room',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('game_room.id'))
)


class User(db.Model, UserMixin):
    def __init__(self, user_name: str, pwd: str):
        self.user_name = user_name
        self.pwd = generate_password_hash(pwd)
        self.add()

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    pwd = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    played_games = db.Column(db.Integer, default=0)
    win_games = db.Column(db.Integer, default=0)
    game_room = db.relationship('GameRoom', backref='creator', lazy=True)

    def __repr__(self):
        return '<User %r>' % self.id

    def check_password(self, password: str):
        return check_password_hash(self.pwd, password)

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as _:
            db.session.rollback()

    def set_stat(self, is_winner: bool = False):
        if is_winner:
            self.win_games += 1
        self.played_games += 1


class GameRoom(db.Model):
    def __init__(self, name: str, pwd: str, players_amount: int, bots_amount: int, creator_name: str):
        self.name = name
        self.pwd = generate_password_hash(pwd)
        self.rules = default_rules
        self.rules['players_amount'] = players_amount
        self.rules['bots_amount'] = bots_amount
        self.set_creator(creator_name)
        self.add()
        self.add_game()

    __tablename__ = 'game_room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    pwd = db.Column(db.String(50), nullable=False)
    rules = db.Column(db.PickleType)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game = db.Column(db.PickleType)
    is_running = db.Column(db.Boolean, default=False)
    is_ended = db.Column(db.Boolean, default=False)
    players = db.relationship("User", secondary=user_room)
    turn_info = db.relationship('TurnInfo', backref='turns', lazy=True)

    def check_password(self, password: str):
        return check_password_hash(self.pwd, password)

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as _:
            db.session.rollback()

    def add_player(self, user_name: str):
        user: User = User.query.filter_by(user_name=user_name).first()
        if user in self.players:
            return True
        if len(self.players) >= self.rules.get('players_amount'):
            return False

        self.players.append(user)
        db.session.commit()
        return True

    def set_creator(self, user_name: str):
        user: User = User.query.filter_by(user_name=user_name).first()
        self.creator_id = user.id
        self.add_player(user_name)

    def add_game(self):
        self.game = Game(self.rules)
        db.session.commit()

    def save(self):
        self.game = copy(self.game)  # fixme это затычка
        db.session.commit()

    def on_join(self) -> dict:
        players_amount = self.rules.get('players_amount')
        players_bots = self.rules.get('bots_amount') + players_amount
        ready_cond = len(self.players) == players_amount and len(self.game.field.players) == players_bots

        return {
            "players": [user.user_name for user in self.players],
            "players_amount": players_amount,
            "bots_amount": self.rules.get('bots_amount'),
            "bots_name": [player.name for player in self.game.field.players if player.is_bot],
            "creator": self.creator.user_name,
            "is_ready": ready_cond,
        }

    def on_start(self):
        self.game.field.sort_players()
        self.game = copy(self.game)
        self.is_running = True
        for player in self.game.field.players:
            self.on_turn(player.name, 'info')
        db.session.commit()

    def on_turn(self, player_name: str, action: str, direction: str | None = None):
        turn_resp, next_player = self.game.make_turn(player_name, action, direction)
        is_win_condition = self.game.is_win_condition(self.rules)
        self.save()
        turn_data = {}
        win_data = {}
        if turn_resp:
            turn_info = TurnInfo(self.id, turn_resp.get_turn_info(), turn_resp.get_info())
            turn_info.save()
            turn_data = {
                'player': turn_info.player_name,
                'action': turn_info.action,
                'direction': turn_info.direction,
                'response': turn_info.turn_response,
                'next_player_name': next_player.name,
            }

            if is_win_condition:
                win_data = self.on_win(player_name)

        return next_player, turn_data, win_data

    def on_get_field(self):
        return {
            'field': self.game.field.get_field_list(),
            'treasures': self.game.field.get_treasures_list(),
            'players': self.game.field.get_players_list(),
        }

    def on_win(self, player_name: str):
        self.is_running = False
        self.is_ended = True
        for player in self.players:
            player.set_stat(player.user_name == player_name)
        turn_info = TurnInfo(self.id, {'player_name': 'System', 'action': 'win'}, player_name)
        turn_info.save()
        win_data = {
            'player': turn_info.player_name,
            'response': turn_info.turn_response,
        }
        return win_data

    def get_turns(self):
        return [turn.to_dict() for turn in self.turn_info]


class TurnInfo(db.Model):
    def __init__(self, room_id: int, info: dict, response: str):
        self.game_room_id = room_id
        self.player_name = info.get('player_name')
        self.action = info.get('action')
        self.direction = info.get('direction')
        self.turn_response = response

    __tablename__ = 'turn_info'
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    game_room_id = db.Column(db.Integer, db.ForeignKey('game_room.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    direction = db.Column(db.String(50))
    turn_response = db.Column(db.PickleType)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'player': self.player_name,
            'action': self.action,
            'direction': self.direction,
            'response': self.turn_response,
        }
