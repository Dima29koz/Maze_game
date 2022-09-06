from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from server.app import db


class User(db.Model, UserMixin):
    """
    This is a User Model

    :param user_name: users nickname
    :type user_name: str
    :param pwd: users password
    :type pwd: str
    :cvar date: date of account creation
    :type date: DateTime
    """

    def __init__(self, user_name: str, user_email: str, pwd: str):
        self.user_name = user_name
        self.user_email = user_email
        self.pwd = generate_password_hash(pwd)
        self.add()

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True)
    user_email = db.Column(db.String(50))
    pwd = db.Column(db.String(256), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

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
        except Exception as e:
            print(e)
            db.session.rollback()

    def set_email(self, new_email: str):
        self.user_email = new_email
        db.session.commit()

    def set_name(self, new_name: str):
        self.user_name = new_name
        db.session.commit()

    def set_pwd(self, new_pwd: str):
        self.pwd = generate_password_hash(new_pwd)
        db.session.commit()


def get_user_by_id(user_id: int) -> User | None:
    """returns user by id if user exists"""
    return User.query.filter_by(id=user_id).first()


def get_user_by_name(user_name: str) -> User | None:
    """returns user by user_name if user exists"""
    return User.query.filter_by(user_name=user_name).first()
