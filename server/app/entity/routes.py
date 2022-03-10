from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import main
from .forms import RegistrationForm, LoginForm
from .models import User


@main.errorhandler(404)
def handle_404(err):
    return render_template('404.html'), 404


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/play')
@login_required
def play():
    return render_template('play.html')


@main.route('/rules')
def rules():
    return render_template('rules.html')


@main.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_name=form.name.data).first()
        if user and check_password_hash(user.pwd, form.pwd.data):
            rm = form.remember.data
            login_user(user, remember=rm)
            return redirect(request.args.get("next") or url_for("main.profile"))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html", form=form)


@main.route('/registration', methods=["POST", "GET"])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        # try:
        hash_pwd = generate_password_hash(form.pwd.data)
        User(user_name=form.username.data, pwd=hash_pwd).add()

        #     db.session.add(user)
        #     db.session.commit()
        # except Exception as e:
        #     db.session.rollback()
        #     print('Error - добавление в бд', e)
        return redirect(url_for('main.login'))
    return render_template('registration.html', form=form)


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@main.route('/game_room')
@login_required
def game_room():
    return render_template('game_room.html')



