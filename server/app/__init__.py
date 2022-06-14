from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO


db = SQLAlchemy()
login_manager = LoginManager()
sio = SocketIO()
migrate = Migrate()

def create_app(config) -> Flask:
    """
    Creates app and register Blueprints

    :returns: app
    :rtype: Flask
    """
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.test_request_context():
        db.create_all()

    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            toolbar = DebugToolbarExtension(app)
        except Exception as e:
            print(e)

    from .main import main as main_blueprint
    from .api import api as api_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint)

    sio.init_app(app, logger=config.LOGGER, manage_session=config.MANAGE_SESSION)

    return app
