import os

app_dir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """
    Base flask-app config object
    """
    DEBUG = False
    LOGGER = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'A SECRET KEY'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class DevelopmentConfig(BaseConfig):
    """
    Development flask-app config object
    """
    DEBUG = True
    LOGGER = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEVELOPMENT_DATABASE_URI') or 'sqlite:///maze.db'
