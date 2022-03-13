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


class User(db.Model, UserMixin):
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


