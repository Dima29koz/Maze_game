import json
import unittest

from dotenv import load_dotenv

load_dotenv()
from server.app import create_app, sio, db
from server.config import TestConfig
from server.app.api_user_account.models import User, get_user_by_id
from server.app.api_game.models import GameRoom, get_room_by_id


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config=TestConfig)
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        self.setUpData()
        with self.app.test_request_context():
            self.c1 = self.app.test_client()
        with self.app.test_request_context():
            self.c2 = self.app.test_client()
        self.loginUsers()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @classmethod
    def setUpData(cls):
        u1 = User('Tester1', 't1@t.t', '1')
        u2 = User('Tester2', 't2@t.t', '1')
        u3 = User('Tester3', 't3@t.t', '1')
        room_name = 'test_room'
        room_pwd = '1'
        room_rules = {
            'num_players': 2,
            'num_bots': 1,
            'is_not_rect': False,
            'is_separated_armory': True,
            'is_diff_outer_concrete_walls': True,
        }

        GameRoom.create(room_name, room_pwd, room_rules, u1)

    def loginUsers(self):
        u1 = {'username': 'Tester1', 'pwd': '1', 'remember': True}
        with self.c1 as c1:
            c1.post('/user_account/login', data=json.dumps(u1), content_type='application/json')
        u2 = {'username': 'Tester2', 'pwd': '1', 'remember': True}
        with self.c2 as c2:
            c2.post('/user_account/login', data=json.dumps(u2), content_type='application/json')


class TestGameRoom(TestCase):

    def test_users_join(self):
        resp1 = self.c1.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token1 = resp1.get_json().get('token')

        client1 = sio.test_client(
            self.app,
            namespace='/game_room',
            auth={'token': token1},
            flask_test_client=self.c1)

        self.assertTrue(client1.is_connected('/game_room'))
        r1 = client1.get_received(namespace='/game_room')

        resp2 = self.c2.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token2 = resp2.get_json().get('token')
        client2 = sio.test_client(
            self.app,
            namespace='/game_room',
            auth={'token': token2},
            flask_test_client=self.c2)

        self.assertTrue(client2.is_connected('/game_room'))
        self.assertNotEqual(client1.eio_sid, client2.eio_sid)
        r2 = client2.get_received(namespace='/game_room')

        self.assertEqual(r1[0].get('name'), 'join')
        self.assertIn({'name': 'Tester1', 'is_spawned': False}, r1[0].get('args')[0].get('players'))
        self.assertEqual(r1[1].get('name'), 'get_spawn')
        self.assertEqual(r1[1].get('args')[0].get('spawn_info'), None)

        self.assertEqual(r2[0].get('name'), 'join')
        self.assertEqual(len(r2[0].get('args')[0].get('players')), 2)
        self.assertEqual(r2[1].get('name'), 'get_spawn')
        self.assertEqual(r2[1].get('args')[0].get('spawn_info'), None)

        r11 = client1.get_received(namespace='/game_room')
        r22 = client2.get_received(namespace='/game_room')
        self.assertEqual(len(r11[0].get('args')[0].get('players')), 2)
        self.assertFalse(r22)

    def test_users_spawn(self):
        room = get_room_by_id(1)
        room.add_player(get_user_by_id(2))

        resp1 = self.c1.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token1 = resp1.get_json().get('token')
        client1 = sio.test_client(self.app, namespace='/game_room', auth={'token': token1}, flask_test_client=self.c1)

        resp2 = self.c2.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token2 = resp2.get_json().get('token')
        client2 = sio.test_client(self.app, namespace='/game_room', auth={'token': token2}, flask_test_client=self.c2)

        self.assertTrue(client1.is_connected('/game_room'))
        self.assertTrue(client2.is_connected('/game_room'))
        self.assertNotEqual(client1.eio_sid, client2.eio_sid)

        client1.get_received(namespace='/game_room')
        client2.get_received(namespace='/game_room')

        client1.emit('set_spawn', {'spawn': {'x': 1, 'y': 1}}, namespace='/game_room')
        r1 = client1.get_received(namespace='/game_room')

        client2.emit('set_spawn', {'spawn': {'x': 2, 'y': 2}}, namespace='/game_room')
        r2 = client2.get_received(namespace='/game_room')
        r11 = client1.get_received(namespace='/game_room')
        r22 = client2.get_received(namespace='/game_room')

        self.assertEqual(r1[0].get('name'), 'join')
        self.assertEqual(r1[0].get('args')[0].get('players')[0].get('is_spawned'), True)

        self.assertEqual(r2[0].get('name'), 'join')
        self.assertEqual(r2[0].get('args')[0].get('players')[0].get('is_spawned'), True)
        self.assertEqual(r2[0].get('args')[0].get('players')[1].get('is_spawned'), False)
        self.assertEqual(r2[1].get('name'), 'join')
        self.assertEqual(r2[1].get('args')[0].get('players')[0].get('is_spawned'), True)
        self.assertEqual(r2[1].get('args')[0].get('players')[1].get('is_spawned'), True)

        self.assertEqual(r11[0].get('name'), 'join')
        self.assertEqual(r11[0].get('args')[0].get('players')[0].get('is_spawned'), True)
        self.assertEqual(r11[0].get('args')[0].get('players')[1].get('is_spawned'), True)
        self.assertEqual(r11[0].get('args')[0].get('is_ready'), True)
        self.assertFalse(r22)

    def test_start(self):
        room = get_room_by_id(1)
        room.add_player(get_user_by_id(2))
        c1 = self.app.test_client()
        c2 = self.app.test_client()
        with c1.session_transaction() as sess1:
            sess1['room_id'] = 1
            sess1['_user_id'] = 1
        with c2.session_transaction() as sess2:
            sess2['room_id'] = 1
            sess2['_user_id'] = 2

        resp1 = self.c1.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token1 = resp1.get_json().get('token')
        client1 = sio.test_client(self.app, namespace='/game_room', auth={'token': token1}, flask_test_client=self.c1)

        resp2 = self.c2.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token2 = resp2.get_json().get('token')
        client2 = sio.test_client(self.app, namespace='/game_room', auth={'token': token2}, flask_test_client=self.c2)

        client1.emit('set_spawn', {'spawn': {'x': 1, 'y': 1}}, namespace='/game_room')
        client2.emit('set_spawn', {'spawn': {'x': 2, 'y': 2}}, namespace='/game_room')
        r1 = client1.get_received(namespace='/game_room')
        client2.get_received(namespace='/game_room')
        self.assertEqual(r1[-1].get('args')[0].get('is_ready'), True)
        client1.emit('start', {'room_id': 1}, namespace='/game_room')
        self.assertEqual(client1.get_received(namespace='/game_room')[0].get('name'), 'start')
        self.assertEqual(client2.get_received(namespace='/game_room')[0].get('name'), 'start')
        room = get_room_by_id(1)
        self.assertEqual(room.is_running, True)
        self.assertEqual(len(room.turns), 3)

    def test_leave(self):
        room = get_room_by_id(1)
        room.add_player(get_user_by_id(2))
        c1 = self.app.test_client()
        c2 = self.app.test_client()
        with c1.session_transaction() as sess1:
            sess1['room_id'] = 1
            sess1['_user_id'] = 1
        with c2.session_transaction() as sess2:
            sess2['room_id'] = 1
            sess2['_user_id'] = 2

        resp1 = self.c1.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token1 = resp1.get_json().get('token')
        client1 = sio.test_client(self.app, namespace='/game_room', auth={'token': token1}, flask_test_client=self.c1)

        resp2 = self.c2.post(
            '/game/join',
            data=json.dumps(dict(name='test_room', pwd='1')),
            content_type='application/json')
        token2 = resp2.get_json().get('token')
        client2 = sio.test_client(self.app, namespace='/game_room', auth={'token': token2}, flask_test_client=self.c2)

        client1.emit('leave', namespace='/game_room')

        r2 = client2.get_received(namespace='/game_room')
        self.assertEqual(len(r2[-1].get('args')[0].get('players')), 1)
        room = get_room_by_id(1)
        self.assertEqual(room.creator.user_name, 'Tester2')
        client2.emit('leave', namespace='/game_room')
        room = get_room_by_id(1)
        self.assertIsNone(room)
