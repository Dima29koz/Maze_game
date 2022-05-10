import unittest

from server.app import create_app, sio, db
from server.config import TestConfig
from server.app.main import models


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config=TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.sio_client = sio.test_client(self.app, flask_test_client=self.client)
        db.create_all()
        self.setUpData()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    @classmethod
    def setUpData(cls):
        u1 = models.User('Tester1', '1')
        u2 = models.User('Tester2', '1')
        room = models.GameRoom('test_room', '1', 2, 1, u1)
        room.add_player(u2)
        room.game.field.spawn_player({'x': 1, 'y': 1}, u1.user_name, 1)
        room.game.field.spawn_player({'x': 1, 'y': 1}, u2.user_name, 1)
        room.save()
        room.on_start()


class TestGame(TestCase):

    def test_initial_turns(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 1
        rv = self.client.get('/api/game_data/1')
        self.assertEqual(len(rv.get_json().get('turns')), 3)
        self.assertEqual(rv.get_json().get('next_player'), 'Tester1')

    def test_initial_players_stat(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 1
        rv = self.client.get('/api/players_stat/1')
        init_stats = [
            {'arrows': 3, 'bombs': 3, 'has_treasure': False, 'health': 2, 'name': 'Tester1'},
            {'arrows': 3, 'bombs': 3, 'has_treasure': False, 'health': 2, 'name': 'Tester2'}]
        self.assertEqual(rv.get_json()[0:2], init_stats)

    def test_action(self):
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
        client.connect(namespace='/game')
        client2.connect(namespace='/game')
        client.emit('join', {'room_id': 1}, namespace='/game')
        client2.emit('join', {'room_id': 1}, namespace='/game')
        client.emit('action', {'action': 'shoot_bow', 'direction': 'bottom'}, namespace='/game')
        rv1 = client.get_received(namespace='/game')[-1]
        rv2 = client2.get_received(namespace='/game')[-1]
        self.assertEqual(rv1, rv2)
        self.assertEqual(rv1.get('args')[0].get('turn_data').get('response').split(',')[0], 'попал')
        self.assertEqual(rv1.get('args')[0].get('players_stat')[0].get('arrows'), 2)
        self.assertEqual(rv1.get('args')[0].get('players_stat')[1].get('health'), 1)

    def test_get_allowed_abilities(self):
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
        client.connect(namespace='/game')
        client2.connect(namespace='/game')
        client.emit('join', {'room_id': 1}, namespace='/game')
        client2.emit('join', {'room_id': 1}, namespace='/game')
        client.emit('get_allowed_abilities', namespace='/game')
        client2.emit('get_allowed_abilities', namespace='/game')
        rv1 = client.get_received(namespace='/game')[-1]
        rv2 = client2.get_received(namespace='/game')[-1]
        self.assertEqual(rv1.get('args')[0].get('is_active'), True)
        self.assertEqual(rv2.get('args')[0].get('is_active'), False)
        self.assertEqual(rv1.get('args')[0].get('next_player_name'), rv2.get('args')[0].get('next_player_name'))
