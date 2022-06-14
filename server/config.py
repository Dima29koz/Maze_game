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
    MANAGE_SESSION = True


class DevelopmentConfig(BaseConfig):
    """
    Development flask-app config object
    """
    DEBUG = True
    LOGGER = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEVELOPMENT_DATABASE_URI') or 'sqlite:///' + os.path.join(app_dir, 'maze.db')


class TestConfig(BaseConfig):
    """
    Test flask-app config object
    """
    TESTING = True
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app_dir, 'test.db')


class ProductionConfig(BaseConfig):
    MANAGE_SESSION = False
    try:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres', 'postgresql', 1)
    except AttributeError:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app_dir, 'maze.db')
