import random
from copy import copy
from datetime import datetime
from typing import Optional

import jwt
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from game_core.bots_ai.core import BotAI
from .. import db

from game_core.game_engine.game import Game
from game_core.game_engine.rules import get_rules
from game_core.game_engine.entities.player import Player
from ..api_user_account.models import User, get_user_by_name

user_room = db.Table(
    'user_room',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('game_room.id'))
)


class GameRoom(db.Model):
    """
    This is a Game Room model. Its contains information about game

    :cvar name: name of a room
    :type name: str
    :cvar pwd: password of a room
    :type pwd: str
    :cvar rules: rules for a room
    :type rules: dict
    :cvar date: date of room creation
    :type date: datetime
    :cvar game_state_id: FK of GameState
    :type game_state_id: int | None
    :cvar is_running: running state
    :type is_running: bool
    :cvar is_ended: ended state
    :type is_ended: bool
    :cvar creator_id: id of room creator
    :type creator_id: int
    :cvar winner_id: id of game winner
    :type winner_id: int | None
    :cvar bot_state_id: FK of BotState
    :type bot_state_id: int
    :type players: list[User]
    """

    def __init__(self, name: str, password: str, rules: dict, creator: User):
        self.name = name
        self.pwd = generate_password_hash(password)
        self.rules = rules
        self.set_creator(creator)
        self.add()
        self.add_game()

    __tablename__ = 'game_room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    pwd = db.Column(db.String(256), nullable=False)
    rules = db.Column(db.PickleType)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    game_state_id = db.Column(db.Integer, db.ForeignKey('game_state.id'), default=None)
    is_running = db.Column(db.Boolean, default=False)
    is_ended = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bot_state_id = db.Column(db.Integer, db.ForeignKey('bot_state.id'), default=None)

    creator = db.relationship("User", foreign_keys=[creator_id])
    winner = db.relationship("User", foreign_keys=[winner_id])
    game_state = db.relationship("GameState", foreign_keys=[game_state_id])
    bot_state = db.relationship("BotState", foreign_keys=[bot_state_id])
    players = db.relationship("User", secondary=user_room, backref=db.backref('games', lazy=True))
    turns = db.relationship('TurnInfo', backref='turns', lazy=True)

    def check_password(self, password: str):
        """
        Verified room password

        :param password: room password
        :type password: str
        :return: result of verification
        :rtype: bool
        """
        return check_password_hash(self.pwd, password)

    @property
    def game(self):
        try:
            game = self.game_state.state
        except AttributeError:
            game = None
        return game

    @property
    def next_player_name(self) -> str | None:
        game = self.game
        if not game or self.is_ended:
            return None
        return game.get_current_player().name

    @property
    def current_player_allowed_abilities(self) -> dict[str, bool] | None:
        game = self.game
        if not game or self.is_ended:
            return None
        return game.get_allowed_abilities_str(game.get_current_player())

    @property
    def players_stats(self) -> list[dict] | None:
        game = self.game
        if not game:
            return None
        return game.get_players_data()

    @classmethod
    def create(cls, room_name: str, room_pwd: str, selected_rules: dict, creator: User) -> 'GameRoom':
        base_rules = get_rules()
        rules = base_rules.copy()

        rules['players_amount'] = selected_rules.get('num_players')
        rules['bots_amount'] = selected_rules.get('num_bots')
        rules['generator_rules']['is_not_rect'] = selected_rules.get('is_not_rect')
        rules['generator_rules']['seed'] = random.random()
        rules['generator_rules']['is_separated_armory'] = selected_rules.get('is_separated_armory')
        rules['gameplay_rules']['diff_outer_concrete_walls'] = selected_rules.get('is_diff_outer_concrete_walls')

        game_room = GameRoom(room_name, room_pwd, rules, creator)
        return game_room

    def gen_token(self, current_user: User) -> str:
        return jwt.encode(
            {'user_id': current_user.id, 'game_id': self.id},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_token(token: str, current_user: User) -> Optional['GameRoom']:
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('user_id') != current_user.id:
                return
        except Exception as _:
            return
        return get_room_by_id(payload.get('game_id'))

    @classmethod
    def validate_rules(cls, selected_rules: dict) -> str | None:
        num_players = selected_rules.get('num_players')
        if num_players < 1 or num_players > 10:
            return 'players amount must be from 1 to 10'
        num_bots = selected_rules.get('num_bots')
        if num_bots < 0 or num_bots > 10:
            return 'bots amount must be from 0 to 10'
        if num_players + num_bots > 10:
            return 'total amount of players and bots must be less than 10'

    def add(self):
        """add room to DB"""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as _:
            print(_)
            db.session.rollback()

    def add_player(self, user: User):
        """
        add player to room

        :return: False if there is no empty slots in a room, else True
        :rtype: bool
        """
        if user in self.players:
            return True
        if len(self.players) >= self.rules.get('players_amount'):
            return False

        self.players.append(user)
        db.session.commit()
        return True

    def remove_player(self, user: User):
        """
        remove player from room

        :return: True if removed and room still exists, else False
        :rtype: bool
        """
        if user not in self.players:
            return False

        self.players.remove(user)
        self.game_state.remove_player(user.user_name)

        if user.id == self.creator_id:
            try:
                self.creator_id = self.players[0].id
            except IndexError:
                db.session.delete(self)
                db.session.commit()
                return False
        self.save()
        return True

    def set_creator(self, user: User):
        """set room creator"""
        self.creator_id = user.id
        self.add_player(user)

    def add_game(self):
        """creates Game() and add it to DB"""
        self.game_state = GameState(self.rules)
        db.session.commit()

    def save(self):
        """updates game object state in DB"""
        self.game_state.save()

    def get_info(self) -> dict:
        """
        returns room data (room settings, players info)

        :return: room data dict
        :rtype: dict
        """
        return {
            "players_amount": self.rules.get('players_amount'),
            "bots_amount": self.rules.get('bots_amount'),
            "creator": self.creator.user_name,
            "is_ready": self.is_ready_to_start(),
            "players": [{
                'name': player.user_name,
                'is_spawned': player.user_name in [player.name for player in self.game_state.state.field.players
                                                   if not player.is_bot],
            } for player in self.players],
            "bots": [{
                'name': bot.name,
                'is_spawned': True,
            } for bot in self.game_state.state.field.players if bot.is_bot],
        }

    def is_ready_to_start(self):
        field = self.game_state.state.field
        is_all_players_joined = len(self.players) == self.rules.get('players_amount')
        is_all_players_spawned = len(field.players) == self.rules.get('bots_amount') + self.rules.get('players_amount')
        return is_all_players_joined and is_all_players_spawned

    def get_winner_name(self) -> str | None:
        if not self.is_ended:
            return None
        if self.winner_id:
            return self.winner.user_name
        else:
            return self.turns[-1].player_name

    def on_start(self):
        """Update room state to `running`, make initial turn for each player"""
        self.game_state.state.field.sort_players()
        self.save()
        if self.rules.get('bots_amount', 0):
            self.bot_state = BotState(self.rules, self.game_state.state.get_players_pos())
        self.is_running = True
        for player in self.game_state.state.field.players:
            self.on_turn(player, 'info')
        db.session.commit()

    def on_turn(self, player: Player, action: str, direction: str | None = None):
        """
        calculates turn feedback;
        append turn info to DB

        :returns: next player obj, turn_data, winner_name[Optional]
        :rtype: (Player, dict, str | None)
        """
        turn_resp, next_player = self.game_state.state.make_turn(action, direction)
        is_win_condition = self.game_state.state.is_win_condition(self.rules)
        self.save()
        turn_data = {}
        winner_name = None
        if turn_resp:
            if self.bot_state:
                self.bot_state.process_turn(turn_resp.get_raw_info())
            turn_info = TurnInfo(self.id, turn_resp.get_turn_info(), turn_resp.get_info())
            turn_info.save()
            turn_data = turn_info.to_dict()

            if is_win_condition:
                winner_name = self._on_win(player)

        return next_player, turn_data, winner_name

    def on_get_field(self) -> dict:
        """returns field data"""
        return {
            'field': self.game_state.state.get_field_list(),
            'treasures': self.game_state.state.get_treasures_list(),
            'players': self.game_state.state.get_players_positions(),
            'rules': self.rules,
            'spawn_points': self.game_state.state.get_spawn_points()
        }

    def _on_win(self, winner: Player) -> str:
        """
        Switch game state to ended;
        set winner id
        """
        self.is_running = False
        self.is_ended = True
        if not winner.is_bot:  # todo None if winner is bot
            user = get_user_by_name(winner.name)
            self.winner_id = user.id if user else None  # todo need to rework for bot-wins case
        else:
            self.winner_id = None
        self.save()
        return winner.name

    def get_turns(self) -> list[dict]:
        """returns list of game turns"""
        return [turn.to_dict() for turn in self.turns]


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


class GameState(db.Model):
    def __init__(self, rules: dict):
        self.state = Game(rules)

    __tablename__ = 'game_state'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.PickleType)

    def save(self):
        self.state = copy(self.state)  # fixme это затычка
        db.session.commit()

    def remove_player(self, player_name: str):
        for player in self.state.field.players:
            if player.name == player_name and not player.is_bot:
                self.state.field.players.remove(player)


class BotState(db.Model):
    def __init__(self, rules: dict, pl_positions: dict):
        self.state = BotAI(rules, pl_positions)

    __tablename__ = 'bot_state'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.PickleType)

    def process_turn(self, raw_response: dict):
        self.state.process_turn_resp(raw_response)
        self.state = copy(self.state)  # fixme это затычка
        db.session.commit()


def get_not_ended_room_by_name(room_name: str) -> GameRoom | None:
    """returns not ended game room by name if room exists"""
    return GameRoom.query.filter_by(name=room_name, is_ended=False).first()


def get_room_by_id(room_id: int) -> GameRoom | None:
    """returns game room by id if room exists"""
    return GameRoom.query.filter_by(id=room_id).first()


def get_user_won_games_amount(user_id: int) -> int:
    """returns amount of user won games"""
    return GameRoom.query.filter_by(winner_id=user_id).count()
