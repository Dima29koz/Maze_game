from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, EqualTo, ValidationError, NumberRange

from .models import get_not_ended_room_by_name
from ..main.models import get_user_by_name


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
    :cvar is_not_rect: field has random form if True
    :type is_not_rect: BooleanField
    :cvar is_separated_armory: different cells for Weapon and Explosive armory
    :type is_separated_armory: BooleanField
    :cvar is_same_wall_outer_concrete: if true you won't know difference between WallConcrete and WallOuter
    :type is_same_wall_outer_concrete: BooleanField
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
    is_not_rect = BooleanField("Поле произвольной формы", default=False, render_kw={'disabled': True})
    is_separated_armory = BooleanField("Раздельные склады оружия и взрывчатки", default=False)
    is_same_wall_outer_concrete = BooleanField("Не различать внешние и внутренние стены", default=False)
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
