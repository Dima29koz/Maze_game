from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    abort,
    redirect,
    url_for,
    current_app,
)
from flask_login import login_user, login_required, logout_user, current_user

from werkzeug.security import check_password_hash, generate_password_hash

from .models import User, db
from .forms import RegistrationForm, LoginForm


module = Blueprint('entity', __name__)


def log_error(*args, **kwargs):
    current_app.logger.error(*args, **kwargs)


@module.route('/')
def index():
    return render_template('index.html')


@module.route('/play')
def play():
    return render_template('play.html')


@module.route('/rules')
def rules():
    return render_template('rules.html')


@module.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_name=form.name.data).first()
        if user and check_password_hash(user.pwd, form.pwd.data):
            rm = form.remember.data
            login_user(user, remember=rm)
            return redirect(request.args.get("next") or url_for("entity.profile"))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", form=form)


@module.route('/registration', methods=["POST", "GET"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hash_pwd = generate_password_hash(form.pwd.data)
            user = User(user_name=form.username.data, pwd=hash_pwd)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error - добавление в бд', e)
        return redirect(url_for('entity.login'))
    return render_template('registration.html', form=form)


@module.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("entity.index"))


@module.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
