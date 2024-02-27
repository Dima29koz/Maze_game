from flask import Blueprint

game = Blueprint('api_game', __name__, url_prefix='/game')

from . import routes, events
