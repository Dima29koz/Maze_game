from flask import Blueprint

user_account = Blueprint('user_account', __name__, url_prefix='/user_account')

from . import routes
