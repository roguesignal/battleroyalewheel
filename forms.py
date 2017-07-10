from app import app
from flask_wtf import FlaskForm

from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import validators
from wtforms import ValidationError

from models import Player
from models import Game
from models import Entry

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
            self.errors['general'] = 'player name ' + str(self.playername.data) + ' already exists'
            valid = False

        if Player.wristband_exists(self.wristband.data):
            self.errors['general'] = 'wristband ' + str(self.wristband.data) + ' already exists'
            valid = False

        if Entry.collar_active(self.collarid.data):
            self.errors['general'] = 'collar ' + str(self.collarid.data) + ' already in use'
            valid = False

        return valid


class ReturnEntryForm(FlaskForm):
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

        if not Player.wristband_exists(self.wristband.data):
            self.errors['general'] = 'wristband ' + str(self.wristband.data) + ' does not exist'
            valid = False

        if Player.wristband_active(self.wristband.data):
            self.errors['general'] = 'wristband ' + str(self.wristband.data) + ' already in game'
            valid = False

        if Entry.collar_active(self.collarid.data):
            self.errors['general'] = 'collar ' + str(self.collarid.data) + ' already in use'
            valid = False

        return valid


class ExitForm(FlaskForm):
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

        p = Player.query.filter(Player.wristband == self.wristband.data).first()
        if not p:
            self.errors['general'] = 'no player with this wristband: ' + self.wristband.data
            valid = False

        if not Entry.collar_active(self.collarid.data):
            self.errors['general'] = 'collar ' + self.collarid.data + ' not associated with an active entry'
            valid = False

        if p.name != Entry.collar_player(self.collarid.data):
            self.errors['general'] = 'collar ' + self.collarid.data + ' does not match player with wristband ' + self.wristband.data
            valid = False

        return valid


class NewGameForm(FlaskForm):
    name = StringField('Name',
            validators=[validators.InputRequired()]
    )
    num_players = IntegerField('# Players',
            validators=[validators.InputRequired()]
    )

    def validate(self):
        valid = FlaskForm.validate(self)
        if not valid:
            return False

        g = Game.query.filter(Game.name == self.name.data).first()
        if g:
            self.errors['general'] = 'game name ' + self.name.data + ' already in use'
            valid = False

        return valid

