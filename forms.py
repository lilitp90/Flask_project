from wtforms import Form, StringField, PasswordField, validators, IntegerField



class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    password = PasswordField('New Password')
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=20)])
    password = PasswordField('New Password')

class ReviewForm(Form):
    rating = IntegerField()
    review = StringField()
