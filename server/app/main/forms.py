from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from server.app.main.models import User, GameRoom


class RegistrationForm(FlaskForm):
    username = StringField('Никнейм: ')
    pwd = PasswordField('Пароль: ', validators=[DataRequired()])
    pwd2 = PasswordField('Повторите пароль: ', validators=[DataRequired(),
                                                           EqualTo('pwd', message='Пароли не совпадают')])
    submit = SubmitField("Регистрация")

    def validate_username(self, username):
        user_obj = User.query.filter_by(user_name=username.data).first()
        if user_obj:
            raise ValidationError('Пользователь с таким ником уже существует')


class LoginForm(FlaskForm):
    name = StringField("Никнейм: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    remember = BooleanField(" Запомнить ", default=False)
    submit = SubmitField("Войти")


class RulesForm(FlaskForm):
    room_name = StringField("Название комнаты: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    submit = SubmitField("Создать")

    def validate_room_name(self, room_name):
        room_obj = GameRoom.query.filter_by(name=room_name.data).first()
        if room_obj:
            raise ValidationError('Комната с таким именем уже существует')


class LoginRoomForm(FlaskForm):
    name = StringField("Название комнаты: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    submit = SubmitField("Войти")

