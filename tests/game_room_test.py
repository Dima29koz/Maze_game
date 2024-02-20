import unittest

from dotenv import load_dotenv

from server.app import create_app, sio, db
from server.app.game.forms import RulesForm

load_dotenv()
from server.config import TestConfig
from server.app.game.models import Game, GameRoom, get_room_by_id
from server.app.main.models import User, get_user_by_id


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config=TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.sio_client = sio.test_client(self.app, flask_test_client=self.client)
        db.drop_all()
        db.create_all()
        self.setUpData()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    @classmethod
    def setUpData(cls):
        u1 = User('Tester1', 't1@t.t', '1')
        u2 = User('Tester2', 't2@t.t', '1')
        u3 = User('Tester3', 't3@t.t', '1')
        rules_form = RulesForm()
        rules_form.room_name.data = 'test_room'
        rules_form.pwd.data = '1'
        rules_form.players_amount.data = 2
        rules_form.bots_amount.data = 1
        GameRoom(rules_form, u1)


class TestGameRoom(TestCase):

    def test_users_join(self):
        c1 = self.app.test_client()
        c2 = self.app.test_client()
        c1.post('/login', data={'name': 'Tester1', 'pwd': '1'}, follow_redirects=True)
        client = sio.test_client(self.app, flask_test_client=c1)
        client.connect(namespace='/game_room')
        self.assertTrue(client.is_connected())
        client.get_received(namespace='/game_room')
        client.emit('join', {'room_id': 1}, namespace='/game_room')
        r1 = client.get_received(namespace='/game_room')

        c2.post('/login', data={'name': 'Tester2', 'pwd': '1'}, follow_redirects=True)
        c2.post('/join', data={'name': 'test_room', 'pwd': '1'}, follow_redirects=True)
        client2 = sio.test_client(self.app, flask_test_client=c2)
        client2.connect(namespace='/game_room')
        self.assertTrue(client2.is_connected())
        self.assertNotEqual(client.eio_sid, client2.eio_sid)
        client2.get_received(namespace='/game_room')
        client2.emit('join', {'room_id': 1}, namespace='/game_room')
        r2 = client2.get_received(namespace='/game_room')

        self.assertEqual(r1[0].get('name'), 'join')
        self.assertIn({'name': 'Tester1', 'is_spawned': False}, r1[0].get('args')[0].get('players'))
        self.assertEqual(r1[1].get('name'), 'get_spawn')
        self.assertEqual(r1[1].get('args')[0].get('spawn_info'), None)

        self.assertEqual(r2[0].get('name'), 'join')
        self.assertEqual(len(r2[0].get('args')[0].get('players')), 2)
        self.assertEqual(r2[1].get('name'), 'get_spawn')
        self.assertEqual(r2[1].get('args')[0].get('spawn_info'), None)

        r11 = client.get_received(namespace='/game_room')
        r22 = client2.get_received(namespace='/game_room')
        self.assertEqual(len(r11[0].get('args')[0].get('players')), 2)
        self.assertFalse(r22)

    def test_users_spawn(self):
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

        client = sio.test_client(self.app, flask_test_client=c1)
        client2 = sio.test_client(self.app, flask_test_client=c2)
        client.connect(namespace='/game_room')
        client2.connect(namespace='/game_room')
        self.assertTrue(client.is_connected())
        self.assertTrue(client2.is_connected())
        self.assertNotEqual(client.eio_sid, client2.eio_sid)
        client.emit('join', {'room_id': 1}, namespace='/game_room')
        client2.emit('join', {'room_id': 1}, namespace='/game_room')
        client.get_received(namespace='/game_room')
        client2.get_received(namespace='/game_room')

        client.emit('set_spawn', {'room_id': 1, 'spawn': {'x': 1, 'y': 1}}, namespace='/game_room')
        r1 = client.get_received(namespace='/game_room')

        client2.emit('set_spawn', {'room_id': 1, 'spawn': {'x': 2, 'y': 2}}, namespace='/game_room')
        r2 = client2.get_received(namespace='/game_room')
        r11 = client.get_received(namespace='/game_room')
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
        client = sio.test_client(self.app, flask_test_client=c1)
        client2 = sio.test_client(self.app, flask_test_client=c2)
        client.connect(namespace='/game_room')
        client2.connect(namespace='/game_room')
        client.emit('join', {'room_id': 1}, namespace='/game_room')
        client2.emit('join', {'room_id': 1}, namespace='/game_room')
        client.emit('set_spawn', {'room_id': 1, 'spawn': {'x': 1, 'y': 1}}, namespace='/game_room')
        client2.emit('set_spawn', {'room_id': 1, 'spawn': {'x': 2, 'y': 2}}, namespace='/game_room')
        r1 = client.get_received(namespace='/game_room')
        client2.get_received(namespace='/game_room')
        self.assertEqual(r1[-1].get('args')[0].get('is_ready'), True)
        client.emit('start', {'room_id': 1}, namespace='/game_room')
        self.assertEqual(client.get_received(namespace='/game_room')[0].get('name'), 'start')
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
        client = sio.test_client(self.app, flask_test_client=c1)
        client2 = sio.test_client(self.app, flask_test_client=c2)
        client.connect(namespace='/game_room')
        client2.connect(namespace='/game_room')
        client.emit('join', {'room_id': 1}, namespace='/game_room')
        client2.emit('join', {'room_id': 1}, namespace='/game_room')

        client.emit('leave', {'room_id': 1}, namespace='/game_room')

        r2 = client2.get_received(namespace='/game_room')
        self.assertEqual(len(r2[-1].get('args')[0].get('players')), 1)
        room = get_room_by_id(1)
        self.assertEqual(room.creator.user_name, 'Tester2')
        client2.emit('leave', {'room_id': 1}, namespace='/game_room')
        room = get_room_by_id(1)
        self.assertIsNone(room)
