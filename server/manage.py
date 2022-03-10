from flask_migrate import Migrate

from app import create_app, sio, db

app = create_app()
app.config.from_object('config.DevelopmentConfig')

migrate = Migrate(app, db)


if __name__ == '__main__':
    sio.run(app)
