from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db, login_manager

login_manager.login_view = 'main.login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    print(db.session.query(User).get(user_id))
    return db.session.query(User).get(user_id)


user_room = db.Table(
    'user_room',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('game_room.id'))
)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    pwd = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.id

    def set_pwd(self, password):
        self.pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwd, password)

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error - добавление в бд', e)


class GameRoom(db.Model):
    __tablename__ = 'game_room'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    pwd = db.Column(db.String(50), nullable=False)
    rules = db.Column(db.PickleType)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    players = db.relationship("User", secondary=user_room)

    def set_pwd(self, password):
        self.pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwd, password)

    def add(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error - добавление в бд', e)

    def add_player(self, user_name):
        user: User = User.query.filter_by(user_name=user_name).first()
        if user in self.players:
            return True
        if not len(self.players) < self.rules.get('players_amount'):
            return False

        self.players.append(user)
        db.session.commit()
        return True
