from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, DecimalField, IntegerField, SelectField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, \
    ValidationError, NumberRange
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email')
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email')
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другое имя пользователя.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой email.')

class EditProfileForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон')
    address = TextAreaField('Адрес')
    submit = SubmitField('Сохранить')

class CheckoutForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email')
    phone = StringField('Телефон', validators=[DataRequired()])
    address = TextAreaField('Адрес доставки', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    postal_code = StringField('Почтовый индекс', validators=[DataRequired()])
    payment_method = RadioField('Способ оплаты', choices=[
        ('card', 'Банковская карта'),
        ('cash', 'Наличными при получении'),
        ('online', 'Онлайн платеж')
    ], validators=[DataRequired()])
    submit = SubmitField('Оформить заказ')