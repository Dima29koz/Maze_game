import unittest
from flask import request, session

from server.app import create_app, db, sio
from server.config import TestConfig
from server.app.main import models


class TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(config=TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.sio_client = sio.test_client(self.app)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def request(self, *args, **kwargs):
        return self.app.test_request_context(*args, **kwargs)


class TestUserAccount(TestCase):

    def registrate(self, username, password, password2):
        data = dict(username=username, pwd=password, pwd2=password2)
        return self.client.post('/registration', data=data, follow_redirects=True)

    def login(self, username, password):
        data = dict(name=username, pwd=password)
        return self.client.post('/login', data=data, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_registration(self):
        rv = self.registrate('Tester', '1', '1')
        self.assertIsNotNone(models.get_user_by_name('Tester'))

    def test_registration_failure_pwd(self):
        rv = self.registrate('Tester', '1', '2')
        self.assertIn('Пароли не совпадают', rv.get_data(as_text=True))

    def test_registration_failure_name(self):
        self.registrate('Tester', '1', '1')
        rv = self.registrate('Tester', '2', '2')
        self.assertIn('Пользователь с таким ником уже существует.', rv.get_data(as_text=True))

    def test_login_logout(self):
        with self.client:
            self.registrate('Tester', '1', '1')
            rv = self.login('Tester', '1')
            self.assertEqual('/profile', rv.request.path)
            self.assertIn('_user_id', session)
            rv = self.logout()
            self.assertEqual('/', rv.request.path)
            self.assertNotIn('_user_id', session)

    def test_login_failure(self):
        self.registrate('Tester', '1', '1')
        rv = self.login('Tester', '2')
        self.assertEqual('/login', rv.request.path)
        self.assertIn('Неверная пара логин/пароль', rv.get_data(as_text=True))
        rv = self.login('Tester1', '1')
        self.assertEqual('/login', rv.request.path)
        self.assertIn('Неверная пара логин/пароль', rv.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
