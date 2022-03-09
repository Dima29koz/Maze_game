from flask import (
    Blueprint,
    render_template,
)

module = Blueprint('general', __name__)


@module.app_errorhandler(404)
def handle_404(err):
    return render_template('404.html'), 404
