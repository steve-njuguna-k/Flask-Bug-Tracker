from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.widgets import TextArea

# user registration form
class RegisterForm(FlaskForm):
    first_name = StringField(
        'first name',
        validators=[
            DataRequired(),
            Length(min=3, max=30)
        ]
    )

    last_name = StringField(
        'last name',
        validators=[
            DataRequired(),
            Length(min=3, max=30)
        ]
    )

    username = StringField(
        'username',
        validators=[
            DataRequired(),
            Length(min=3, max=30)
        ]
    )

    email = StringField(
        'email',
        validators=[
            DataRequired(),
            Length(min=10, max=50),
            Email()
        ]
    )

    password = PasswordField(
        'password',
        validators=[DataRequired()]
    )

    confirm_password = PasswordField(
        'confirm password',
        validators=[EqualTo('password')]
    )

    submit = SubmitField('register')

# user login form
class LoginForm(FlaskForm):
    username = StringField(
        'username',
        validators=[
            DataRequired(),
            Length(min=3, max=30)
        ]
    )

    password = PasswordField(
        'password',
        validators=[DataRequired()]
    )

    submit = SubmitField('login')

# posting a bug form
class PostBug(FlaskForm):
    title = StringField(
        'title',
        validators=[
            DataRequired(),
            Length(min=50, max=100)
        ]
    )

    description = StringField(
        'bug summary',
        validators=[
            DataRequired(),
            Length(min=50, max=220)
        ],
        widget=TextArea()
    )

    # catergory - tags
    tags = StringField(
        'tags',
        validators=[
            DataRequired(),
            Length(min=2, max=25)
        ]
    )
    
# updating a bug form
class UpdateBug(FlaskForm):
    title = StringField(
        'title',
        validators=[
            DataRequired(),
            Length(min=50, max=100)
        ]
    )

    description = StringField(
        'bug summary',
        validators=[
            DataRequired(),
            Length(min=50, max=220)
        ],
        widget=TextArea()
    )

    # catergory - tags
    tags = StringField(
        'tags',
        validators=[
            DataRequired(),
            Length(min=2, max=25)
        ]
    )