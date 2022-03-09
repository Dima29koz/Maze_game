from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, StopValidation


class UsernameCheck:
    def __init__(self, lst=None, message=None):
        self.lst = lst
        if not message:
            message = 'Пользователь с таким ником уже существует'
        self.message = message

    def __call__(self, form, field):
        if field.data in self.lst:
            raise StopValidation(self.message)


class RegistrationForm(FlaskForm):
    def __init__(self, lst, **kwargs):
        super().__init__(**kwargs)
        self.name.validators = [DataRequired('Поле не заполнено'), UsernameCheck(lst)]

    name = StringField('Никнейм: ')
    pwd = PasswordField('Пароль: ', validators=[DataRequired()])
    pwd2 = PasswordField('Повторите пароль: ', validators=[DataRequired(),
                                                           EqualTo('pwd', message='Пароли не совпадают')])
    submit = SubmitField("Регистрация")


class LoginForm(FlaskForm):
    name = StringField("Никнейм: ", validators=[DataRequired('Поле не заполнено')])
    pwd = PasswordField("Пароль: ", validators=[DataRequired('Поле не заполнено')])
    remember = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")
