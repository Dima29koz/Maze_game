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
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


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
    LOGGER = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app_dir, 'maze.db')
