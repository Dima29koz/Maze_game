from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, StopValidation, ValidationError

from server.app.entity.models import User


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
