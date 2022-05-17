import os
from flask_migrate import Migrate

from app import create_app, sio, db
import config

app = create_app(os.environ.get('FLASK_ENV') or config.DevelopmentConfig)
migrate = Migrate(app, db)


if __name__ == '__main__':
    sio.run(app)
    # db.create_all(app=app)
