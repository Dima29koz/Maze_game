from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError, NumberRange

from .models import get_user_by_name, get_not_ended_room_by_name


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


class RulesForm(FlaskForm):
    """
    Rules form

    :cvar room_name: room name
    :type room_name: StringField
    :cvar pwd: room password
    :type pwd: PasswordField
    :cvar players_amount: amount of players in a room
    :type players_amount: IntegerField
    :cvar bots_amount: amount of players in a room
    :type bots_amount: IntegerField
    :cvar submit: submit field
    :type submit: SubmitField
    """
    room_name = StringField("Название комнаты: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    players_amount = IntegerField("Число игроков", validators=[DataRequired('Поле не заполнено')], default=2)
    bots_amount = IntegerField(
        "Число ботов",
        validators=[NumberRange(min=0, max=10, message='Число ботов должно быть от 0 до 10')],
        default=0,
        render_kw={'disabled': False})
    submit = SubmitField("Создать")

    def validate_room_name(self, room_name: StringField):
        """
        room_name validator

        :param room_name: room name
        :type room_name: StringField
        :raises ValidationError: if room_name is already taken
        """
        if get_not_ended_room_by_name(room_name.data):
            raise ValidationError('Комната с таким именем уже существует')


class LoginRoomForm(FlaskForm):
    """
    LoginRoom form

    :cvar name: room name
    :type name: StringField
    :cvar pwd: room password
    :type pwd: PasswordField
    :cvar submit: submit field
    :type submit: SubmitField
    """
    name = StringField("Название комнаты: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    submit = SubmitField("Войти")

    def validate_name(self, name: StringField):
        """
        room_name validator

        :param name: room name
        :type name: StringField
        :raises ValidationError: if room_name is incorrect
        """
        room_obj = get_not_ended_room_by_name(name.data)
        if not room_obj:
            raise ValidationError('Комнаты с таким именем не существует')

    def validate_pwd(self, pwd: PasswordField):
        """
        room password validator

        :param pwd: room password
        :type pwd: PasswordField
        :raises ValidationError: if room_name or password is incorrect
        """
        room_obj = get_not_ended_room_by_name(self.name.data)
        if not room_obj or not room_obj.check_password(pwd.data):
            raise ValidationError('Неверная пара название/пароль')
