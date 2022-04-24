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
    """
    This is a User Model

    :param user_name: users nickname
    :type user_name: str
    :param pwd: users password
    :type user_name: str
    :cvar date: date of account creation
    :type date: DateTime
    :cvar played_games: amount of user ended games
    :type played_games: int
    :cvar win_games: amount of user won games
    :type win_games: int
    """
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
        """
        Verified users password.

        :param password: user password
        :type password: str
        :return: result of verification
        :rtype: bool
        """
        return check_password_hash(self.pwd, password)

    def add(self):
        """added user to DB"""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as _:
            db.session.rollback()

    def set_stat(self, is_winner: bool = False):
        """Updates user stat after game"""
        if is_winner:
            self.win_games += 1
        self.played_games += 1


class GameRoom(db.Model):
    """
    This is a Game Room model. Its contains information about game

    :param name: name of a room
    :type name: str
    :param pwd: password of a room
    :type pwd: str
    :cvar rules: rules of a room
    :type rules: dict
    :cvar date: date of room creation
    :type date: DateTime
    :cvar creator_id: id of room creator
    :type creator_id: int
    :cvar game: game object
    :type game: Game
    :cvar is_running: running state
    :type is_running: bool
    :cvar is_ended: ended state
    :type is_ended: bool
    """
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
        """
        Verified room password

        :param password: room password
        :type password: str
        :return: result of verification
        :rtype: bool
        """
        return check_password_hash(self.pwd, password)

    def add(self):
        """add room to DB"""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as _:
            db.session.rollback()

    def add_player(self, user_name: str):
        """
        add player to room

        :return: False if there is no empty slots in a room, else True
        :rtype: bool
        """
        user: User = User.query.filter_by(user_name=user_name).first()
        if user in self.players:
            return True
        if len(self.players) >= self.rules.get('players_amount'):
            return False

        self.players.append(user)
        db.session.commit()
        return True

    def remove_player(self, user_name: str):
        """
        remove player from room

        :return: True if removed, else False
        :rtype: bool
        """
        user: User = User.query.filter_by(user_name=user_name).first()
        if user not in self.players:
            return False

        self.players.remove(user)
        for player in self.game.field.players:
            if player.name == user.user_name:
                self.game.field.players.remove(player)
        self.save()
        return True

    def set_creator(self, user_name: str):
        """set room creator"""
        user: User = User.query.filter_by(user_name=user_name).first()
        self.creator_id = user.id
        self.add_player(user_name)

    def add_game(self):
        """creates Game() and add it to DB"""
        self.game = Game(self.rules)
        db.session.commit()

    def save(self):
        """updates game object state in DB"""
        self.game = copy(self.game)  # fixme это затычка
        db.session.commit()

    def on_join(self) -> dict:
        """
        triggers when player (client) joins room

        :return: room data dict
        :rtype: dict
        """
        field = self.game.field
        is_all_players_joined = len(self.players) == self.rules.get('players_amount')
        is_all_players_spawned = len(field.players) == self.rules.get('bots_amount') + self.rules.get('players_amount')
        return {
            "players_amount": self.rules.get('players_amount'),
            "bots_amount": self.rules.get('bots_amount'),
            "creator": self.creator.user_name,
            "is_ready": is_all_players_joined and is_all_players_spawned,
            "players": [{
                'name': player.user_name,
                'is_spawned': player.user_name in [player.name for player in self.game.field.players],
            } for player in self.players],
            "bots": [{
                'name': bot.name,
                'is_spawned': True,
            } for bot in self.game.field.players if bot.is_bot],
        }

    def on_start(self):
        """Update room state to `running`, make initial turn for each player"""
        self.game.field.sort_players()
        self.game = copy(self.game)
        self.is_running = True
        for player in self.game.field.players:
            self.on_turn(player.name, 'info')
        db.session.commit()

    def on_turn(self, player_name: str, action: str, direction: str | None = None):
        """
        calculates turn feedback;
        append turn info to DB

        :returns: next player name, turn_data, win_data[Optional]
        :rtype: (Player, dict, dict | None)
        """
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

    def on_get_field(self) -> dict:
        """returns field data"""
        return {
            'field': self.game.field.get_field_list(),
            'treasures': self.game.field.get_treasures_list(),
            'players': self.game.field.get_players_list(),
        }

    def on_win(self, player_name: str) -> dict:
        """
        Switch game state to ended;
        update player stat
        makes `system turn`
        """
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

    def get_turns(self) -> list[dict]:
        """returns list of game turns"""
        return [turn.to_dict() for turn in self.turn_info]


class TurnInfo(db.Model):
    """
    This is a TurnInfo model

    :cvar player_name: current player name
    :type player_name: str
    :cvar game_room_id: current room id
    :type game_room_id: int
    :cvar action: current player action
    :type action: str
    :cvar direction: current player direction
    :type direction: str
    :cvar turn_response: turns feedback
    :type turn_response: str
    :cvar date: date of turn
    :type date: DateTime
    """
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
        """save turn to DB"""
        db.session.add(self)
        db.session.commit()

    def to_dict(self) -> dict:
        """returns turn info converted to dict"""
        return {
            'player': self.player_name,
            'action': self.action,
            'direction': self.direction,
            'response': self.turn_response,
        }
