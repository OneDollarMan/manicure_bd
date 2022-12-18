from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeLocalField, SubmitField, PasswordField, DecimalField, TimeField, \
    DateField, SelectMultipleField
from wtforms.validators import Length, NumberRange, InputRequired, Optional, ValidationError

rus_length = Length(min=1, max=45, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_number_range = NumberRange(min=1, max=99999999999, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_input_required = InputRequired(message='Заполните поле')
rus_price_range = NumberRange(min=1, max=10000, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_percent_range = NumberRange(min=1, max=100, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')


def date_check(form, field):
    if field.data < datetime.today():
        raise ValidationError('Введите не прошедшую дату')


class LoginForm(FlaskForm):
    login = StringField('Логин', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    otp = StringField('OTP (опционально)', [Optional()])
    submit = SubmitField('Войти')


class FaForm(FlaskForm):
    otp = StringField('Введите OTP из приложения Google', [rus_input_required])
    submit = SubmitField('Включить')


class UserForm(FlaskForm):
    username = StringField('Имя пользователя', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    fio = StringField('ФИО', [rus_input_required, rus_length])
    role = SelectField('Роль', [rus_input_required])
    submit = SubmitField('Добавить')


class ServiceForm(FlaskForm):
    name = StringField('Название', [rus_input_required, rus_length])
    price = DecimalField('Цена', [rus_input_required, rus_number_range])
    duration = TimeField('Длительность', [rus_input_required])
    submit = SubmitField('Добавить')


class ClientForm(FlaskForm):
    first_name = StringField('Имя', [rus_input_required, rus_length])
    number = DecimalField('Номер телефона', [rus_input_required, rus_number_range])
    submit = SubmitField('Добавить')


class OrderForm(FlaskForm):
    date = DateTimeLocalField('Дата', format='%Y-%m-%dT%H:%M', validators=[rus_input_required, date_check])
    user = SelectField('Выберите мастера', validators=[rus_input_required])
    client = SelectField('Выберите клиента', validators=[rus_input_required])
    services = SelectMultipleField('Выберите услуги', validators=[rus_input_required], coerce=int)
    submit = SubmitField('Добавить')


class FilterOrderForm(FlaskForm):
    user = SelectField('Выберите мастера', [Optional()])
    client = SelectField('Выберите клиента', [Optional()])
    date1 = DateTimeLocalField('Дата от', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    date2 = DateTimeLocalField('Дата до', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    submit2 = SubmitField('Показать')


class StatusForm(FlaskForm):
    status = SelectField('Выберите статус', validators=[rus_input_required])
    submit = SubmitField('Изменить')
