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
from models import Entry
from models import Collar

#### helpers

#### custom validators

# user does not exist in database
def vld_new_user(form, field):
    if Player.user_exists(field.data):
        raise ValidationError('username %s already exists.' % field.data)

#### custom forms

class NewEntryForm(FlaskForm):
    playername = StringField('Player Name',
            validators=[validators.InputRequired()]
    )
    wristband = StringField('Wristband #',
            validators=[validators.InputRequired()]
    )
    collarid = StringField('Collar ID',
            validators=[validators.InputRequired()]
    )

    def validate(self):
        valid = FlaskForm.validate(self)
        if not valid:
            return False

        if Player.player_exists(self.playername.data):
            self.errors['general'] = 'player name already exists'
            return False

        if Player.wristband_exists(self.wristband.data):
            self.errors['general'] = 'wristband already exists'
            return False

        collar = Collar.query.filter(Collar.collar_id == self.collarid.data.strip()).first()
        #### TODO: change this if we want collar ids created on the fly
        if not collar:
            self.errors['general'] = 'invalid collar id'
            return False
        else:
            if collar.entry.active:
                self.errors['general'] = 'collar is already in use'
                return False

        return True


class ReturnEntryForm(FlaskForm):
    wristband = StringField('Wristband #',
            validators=[validators.InputRequired()]
    )
    collarid = StringField('Collar ID',
            validators=[validators.InputRequired()]
    )

    ## VALIDATION
    # wristband must exist in database
    # collarid must be unused


class ExitForm(FlaskForm):
    pass

class NewGameForm(FlaskForm):
    pass

class UpdateGameForm(FlaskForm):
    pass

class UpdatePlayerForm(FlaskForm):
    pass


