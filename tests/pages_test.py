import json
import unittest

from dotenv import load_dotenv
from flask import session

load_dotenv()
import server.app.api_user_account.models
from server.app import create_app, db, sio
from server.config import TestConfig
from server.app.api_game import models


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config=TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.sio_client = sio.test_client(self.app, flask_test_client=self.client)
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def request(self, *args, **kwargs):
        return self.app.test_request_context(*args, **kwargs)

    def registrate(self, username: str, user_email: str, password: str, password2: str):
        data = dict(username=username, user_email=user_email, pwd=password, pwd_repeat=password2)
        return self.client.post('/user_account/registration', data=json.dumps(data), content_type='application/json')

    def login(self, username: str, password: str):
        data = dict(username=username, pwd=password, remember=False)
        return self.client.post('/user_account/login', data=json.dumps(data), content_type='application/json')

    def logout(self):
        return self.client.get('/user_account/logout')

    def create_room(self, room_name, room_pwd, players_amount, bots_amount):
        room_rules = {
            'num_players': players_amount,
            'num_bots': bots_amount,
            'is_not_rect': False,
            'is_separated_armory': True,
            'is_diff_outer_concrete_walls': True,
        }
        data = dict(name=room_name, pwd=room_pwd, rules=room_rules)
        return self.client.post('/game/create', data=json.dumps(data), content_type='application/json')

    def join_room(self, room_name, room_pwd):
        data = dict(name=room_name, pwd=room_pwd)
        return self.client.post('/game/join', data=json.dumps(data), content_type='application/json')


class TestUserAccount(TestCase):

    def test_registration(self):
        rv = self.registrate('Tester', 't1@t.t', '1', '1')
        self.assertIsNotNone(server.app.api_user_account.models.get_user_by_name('Tester'))

    def test_registration_failure_pwd(self):
        rv = self.registrate('Tester', 't1@t.t', '1', '2')
        self.assertIn('passwords must match', rv.get_json().get('msg'))

    def test_registration_failure_name(self):
        self.registrate('Tester', 't1@t.t', '1', '1')
        rv = self.registrate('Tester', 't1@t.t', '2', '2')
        self.assertIn('username is not allowed', rv.get_json().get('msg'))

    def test_login_logout(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            rv = self.login('Tester', '1')
            self.assertEqual('/user_account/login', rv.request.path)
            self.assertIn('_user_id', session)
            rv = self.logout()
            self.assertIn('logout successful', rv.get_json().get('msg'))
            self.assertNotIn('_user_id', session)

    def test_login_failure(self):
        self.registrate('Tester', 't1@t.t', '1', '1')
        rv = self.login('Tester', '2')
        self.assertEqual('/user_account/login', rv.request.path)
        self.assertIn('Wrong username or password', rv.get_json().get('msg'))
        rv = self.login('Tester1', '1')
        self.assertEqual('/user_account/login', rv.request.path)
        self.assertIn('Wrong username or password', rv.get_json().get('msg'))


class TestGameRoomJoinCreate(TestCase):

    def test_room_creation(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            rv = self.create_room('test_room', '1', 2, 1)
            self.assertIsNotNone(models.get_not_ended_room_by_name('test_room'))
            self.assertEqual(models.get_not_ended_room_by_name('test_room').creator.user_name, 'Tester')
            self.assertIn(
                server.app.api_user_account.models.get_user_by_name('Tester'),
                models.get_not_ended_room_by_name('test_room').players)
            self.assertEqual(1, rv.get_json().get('id'))
            self.assertEqual('test_room', rv.get_json().get('name'))
            self.assertIn('token', rv.get_json())

    def test_room_creation_failure_bots_amount(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            rv = self.create_room('test_room', '1', 2, -1)
            self.assertIsNone(models.get_not_ended_room_by_name('test_room'))
            self.assertIn('bots amount must be from 0 to 10', rv.get_json())

            rv = self.create_room('test_room', '1', 2, 11)
            self.assertIsNone(models.get_not_ended_room_by_name('test_room'))
            self.assertIn('bots amount must be from 0 to 10', rv.get_json())

            rv = self.create_room('test_room', '1', 5, 6)
            self.assertIsNone(models.get_not_ended_room_by_name('test_room'))
            self.assertIn('total amount of players and bots must be less than 10', rv.get_json())

    def test_room_creation_failure_room_name(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            self.create_room('test_room', '1', 2, 1)
            rv = self.create_room('test_room', '1', 1, 2)
            self.assertIn('Room with this name already exists', rv.get_json())

    def test_room_join(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.registrate('Tester2', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            self.create_room('test_room', '1', 2, 1)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = 2

        with self.client:
            self.login('Tester2', '1')
            rv = self.join_room('test_room', '1')

            self.assertEqual(1, rv.get_json().get('id'))
            self.assertEqual('test_room', rv.get_json().get('name'))
            self.assertEqual('created', rv.get_json().get('state'))
            self.assertIn('token', rv.get_json())
            self.assertIn(
                server.app.api_user_account.models.get_user_by_name('Tester2'),
                models.get_not_ended_room_by_name('test_room').players)

    def test_room_join_failure_name_pwd(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.registrate('Tester2', 't1@t.t', '1', '1')
            self.login('Tester', '1')
            self.create_room('test_room', '1', 2, 1)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = 2

        with self.client:
            rv = self.join_room('test_room', '2')
            self.assertIn('Wrong room name or password', rv.get_json().get('msg'))
            rv = self.join_room('test_room2', '1')
            self.assertIn('Wrong room name or password', rv.get_json().get('msg'))


class TestProfile(TestCase):

    def test_user_games(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.registrate('Tester2', 't1@t.t', '1', '1')
            self.login('Tester', '1')
            r = self.create_room('test_room1', '1', 2, 1)
            room = models.get_not_ended_room_by_name('test_room1')
            room.is_ended = True
            room.winner_id = 1
            room.save()
            self.create_room('test_room2', '1', 2, 1)
            room = models.get_not_ended_room_by_name('test_room2')
            room.is_running = True
            room.save()
            self.create_room('test_room1', '1', 2, 1)
            res_dict = {'games': [
                {'details': 'details', 'id': 1, 'name': 'test_room1', 'status': 'ended', 'winner': 'Tester'},
                {'details': 'details', 'id': 2, 'name': 'test_room2', 'status': 'running', 'winner': '-'},
                {'details': 'details', 'id': 3, 'name': 'test_room1', 'status': 'created', 'winner': '-'}
            ], 'games_total': 3, 'games_won': 1}
            rv = self.client.get('/user_account/user_games')
            self.assertDictEqual(rv.get_json(), res_dict)


if __name__ == '__main__':
    unittest.main()
