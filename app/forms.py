from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField(label='Email Address', validators=[DataRequired(), Email(message='⚠️ Enter A Valid Email Address!')], render_kw={"placeholder": "Email Address"})
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=6, max=255,  message='⚠️ Password strength must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Password"})
    show_password = BooleanField('Show password', id='check')
    submit = SubmitField(label=('Log In'))

class RegisterForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired(), Length(min=3, max=255,  message='⚠️ Username length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Username"})
    email = StringField(label='Email Address', validators=[DataRequired(), Email(message='⚠️ Enter A Valid Email Address!')], render_kw={"placeholder": "Email Address"})
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=6, max=255,  message='⚠️ Password strength must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), EqualTo('password', message='⚠️ The Passwords Entered Do Not Match!')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField(label=('Sign Up'))

class CreatePostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(), Length(min=3, max=255,  message='⚠️ Title length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Title"})
    description = TextAreaField(label='Description', validators=[DataRequired(), Length(min=3, max=10000,  message='⚠️ Description length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Description", 'rows': 10})
    tags = StringField(label='Tags', validators=[DataRequired(), Length(min=3, max=255,  message='⚠️ Tags length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Tags"})
    submit = SubmitField(label=('Submit'))

class UpdatePostForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired(), Length(min=3, max=255,  message='⚠️ Title length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Title"})
    description = TextAreaField(label='Description', validators=[DataRequired(), Length(min=3, max=10000,  message='⚠️ Description length must be between %(min)d and %(max)d characters!')], render_kw={"placeholder": "Description", 'rows': 10})
    bug_status = SelectField(label='Select Status',choices=[
        ('Resolved', 'Resolved'),
        ('In Progress', 'In Progress'),
        ('Unresolved', 'Unresolved')
    ], render_kw={"placeholder": "Choose Status"})
    submit = SubmitField(label=('Submit'))