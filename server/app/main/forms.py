from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from server.app.main.models import get_user_by_name


class RegistrationForm(FlaskForm):
    """
    Registration form

    :cvar username: user nickname
    :type username: StringField
    :cvar pwd: user password
    :type pwd: PasswordField
    :cvar pwd2: user password repeat
    :type pwd2: PasswordField
    :cvar submit: submit field
    :type submit: SubmitField
    """
    username = StringField('Никнейм: ')
    pwd = PasswordField('Пароль: ', validators=[DataRequired()])
    pwd2 = PasswordField('Повторите пароль: ', validators=[DataRequired(),
                                                           EqualTo('pwd', message='Пароли не совпадают')])
    submit = SubmitField("Регистрация")

    def validate_username(self, username: StringField):
        """
        username validator

        :param username: user nickname
        :type username: StringField
        :raises ValidationError: if nickname is already taken
        """
        user_obj = get_user_by_name(username.data)
        if user_obj:
            raise ValidationError('Пользователь с таким ником уже существует')


class LoginForm(FlaskForm):
    """
    Login form

    :cvar name: user nickname
    :type name: StringField
    :cvar pwd: user password
    :type pwd: PasswordField
    :cvar remember: remembers users for the duration of the session
    :type remember: BooleanField
    :cvar submit: submit field
    :type submit: SubmitField
    """
    name = StringField("Никнейм: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    remember = BooleanField(" Запомнить ", default=False)
    submit = SubmitField("Войти")