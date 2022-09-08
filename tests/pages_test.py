import unittest
from flask import request, session

import server.app.main.models
from server.app import create_app, db, sio
from server.config import TestConfig
from server.app.game import models


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
        data = dict(username=username, user_email=user_email, pwd=password, pwd2=password2)
        return self.client.post('/registration', data=data, follow_redirects=True)

    def login(self, username: str, password: str):
        data = dict(name=username, pwd=password)
        return self.client.post('/login', data=data, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def create_room(self, room_name, room_pwd, players_amount, bots_amount):
        data = dict(room_name=room_name, pwd=room_pwd, players_amount=players_amount, bots_amount=bots_amount)
        return self.client.post('/create', data=data, follow_redirects=True)

    def join_room(self, room_name, room_pwd):
        data = dict(name=room_name, pwd=room_pwd)
        return self.client.post('/join', data=data, follow_redirects=True)


class TestUserAccount(TestCase):

    def test_registration(self):
        rv = self.registrate('Tester', 't1@t.t', '1', '1')
        self.assertIsNotNone(server.app.main.models.get_user_by_name('Tester'))

    def test_registration_failure_pwd(self):
        rv = self.registrate('Tester', 't1@t.t', '1', '2')
        self.assertIn('Пароли не совпадают', rv.get_data(as_text=True))

    def test_registration_failure_name(self):
        self.registrate('Tester', 't1@t.t', '1', '1')
        rv = self.registrate('Tester', 't1@t.t', '2', '2')
        self.assertIn('Пользователь с таким ником уже существует.', rv.get_data(as_text=True))

    def test_login_logout(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            rv = self.login('Tester', '1')
            self.assertEqual('/profile', rv.request.path)
            self.assertIn('_user_id', session)
            rv = self.logout()
            self.assertEqual('/', rv.request.path)
            self.assertNotIn('_user_id', session)

    def test_login_failure(self):
        self.registrate('Tester', 't1@t.t', '1', '1')
        rv = self.login('Tester', '2')
        self.assertEqual('/login', rv.request.path)
        self.assertIn('Неверная пара логин/пароль', rv.get_data(as_text=True))
        rv = self.login('Tester1', '1')
        self.assertEqual('/login', rv.request.path)
        self.assertIn('Неверная пара логин/пароль', rv.get_data(as_text=True))


class TestGameRoomJoinCreate(TestCase):

    def test_room_creation(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            rv = self.create_room('test_room', '1', 2, 1)
            self.assertIsNotNone(models.get_not_ended_room_by_name('test_room'))
            self.assertEqual(models.get_not_ended_room_by_name('test_room').creator.user_name, 'Tester')
            self.assertIn(
                server.app.main.models.get_user_by_name('Tester'),
                models.get_not_ended_room_by_name('test_room').players)
            self.assertEqual('/game_room', rv.request.path)
            self.assertIn('room', rv.request.args)
            self.assertEqual('test_room', rv.request.args.get('room'))

    def test_room_creation_failure_bots_amount(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            rv = self.create_room('test_room', '1', 2, -1)
            self.assertIsNone(models.get_not_ended_room_by_name('test_room'))
            self.assertIn('Число ботов должно быть от 0 до 10', rv.get_data(as_text=True))

            rv = self.create_room('test_room', '1', 2, 11)
            self.assertIsNone(models.get_not_ended_room_by_name('test_room'))
            self.assertIn('Число ботов должно быть от 0 до 10', rv.get_data(as_text=True))

    def test_room_creation_failure_room_name(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            self.create_room('test_room', '1', 2, 1)
            rv = self.create_room('test_room', '1', 1, 2)
            self.assertIn('Комната с таким именем уже существует', rv.get_data(as_text=True))

    def test_room_join(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.registrate('Tester2', 't1@t.t', '1', '1')
            self.login('Tester', '1')

            self.create_room('test_room', '1', 2, 1)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = 2

        with self.client:
            rv = self.join_room('test_room', '1')
            self.assertEqual('/game_room', rv.request.path)
            self.assertIn('<h1>Комната: <span id="get-room-name">test_room</span></h1>', rv.get_data(as_text=True))
            self.assertIn(
                server.app.main.models.get_user_by_name('Tester2'),
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
            self.assertIn('Неверная пара название/пароль', rv.get_data(as_text=True))
            rv = self.join_room('test_room2', '1')
            self.assertIn('Комнаты с таким именем не существует', rv.get_data(as_text=True))


class TestProfile(TestCase):

    def test_user_games(self):
        with self.client:
            self.registrate('Tester', 't1@t.t', '1', '1')
            self.registrate('Tester2', 't1@t.t', '1', '1')
            self.login('Tester', '1')
            self.create_room('test_room1', '1', 2, 1)
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
            rv = self.client.get('/api/user_games')
            self.assertDictEqual(rv.get_json(), res_dict)


if __name__ == '__main__':
    unittest.main()
