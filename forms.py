from app import app
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import FieldList
from wtforms import FormField
from wtforms import HiddenField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators
from wtforms import ValidationError

from models import Player
from models import Game

#### helpers

#### custom validators

# user does not exist in database
def vld_new_user(form, field):
    if Player.user_exists(field.data):
        raise ValidationError('username %s already exists.' % field.data)

#### custom forms

class NewEntryForm(FlaskForm):
    pass

class ReturnEntryForm(FlaskForm):
    pass

class ExitForm(FlaskForm):
    pass

class NewGameForm(FlaskForm):
    pass

class UpdateGameForm(FlaskForm):
    pass

class UpdatePlayerForm(FlaskForm):
    pass


