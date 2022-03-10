from flask import Flask
from flask_login import LoginManager

from .database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'entity.login'
    login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
    login_manager.login_message_category = "error"

    from server.app.entity.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.test_request_context():
        db.create_all()

    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            toolbar = DebugToolbarExtension(app)
        except Exception:
            pass

    import server.app.entity.controllers as entity
    import server.app.general.controllers as general

    app.register_blueprint(general.module)
    app.register_blueprint(entity.module)

    return app
