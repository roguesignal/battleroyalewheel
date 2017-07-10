from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime

from datetime import datetime

class utcnow(expression.FunctionElement):
    type = DateTime()

@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

db = SQLAlchemy()

class Base(db.Model, AbstractConcreteBase):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=utcnow())
    updated_on = db.Column(db.DateTime, default=utcnow(), onupdate=utcnow())


class Player(Base):
    __tablename__ = 'player'
    
    name = db.Column(db.String(), index=True, unique=True)
    wristband = db.Column(db.String(), unique=True)
    total_time_played = db.Column(db.Interval())
    num_exits = db.Column(db.Integer())
    entries = db.relationship('Entry', backref='Player')

    def __init__(self, name, wristband):
        self.name = name 
        self.wristband = wristband
        self.total_time_played = timedelta(0)
        self.num_exits = 0

    def __repr__(self):
        return '<Player {}>'.format(self.name)

    def active_entry(self):
        return Entry.query.filter(Entry.player_name == self.name, Entry.active == True).first()

    @classmethod
    def player_exists(cls, name):
        p = Player.query.filter(Player.name == name).first()
        if p:
            return True
        return False

    @classmethod
    def wristband_exists(cls, wristband):
        p = Player.query.filter(Player.wristband == wristband).first()
        if p:
            return True
        return False

    @classmethod
    def wristband_active(cls, wristband):
        p = Player.query.filter(Player.wristband == wristband).first()
        e = Entry.query.filter(Entry.player_name == p.name, Entry.active == True).first()
        if e:
            return True
        return False

    @classmethod
    def player_wristband(cls, wristband):
        return Player.query.filter(Player.wristband == wristband).one_or_none()

class Entry(Base):
    """ Data related to a player's entry in the competition. """
    __tablename__ = 'entry'

    player_name = db.Column(db.String(), db.ForeignKey('player.name'))
    exit_time = db.Column(db.DateTime())
    grace_until = db.Column(db.DateTime())
    num_plays = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    collar = db.Column(db.String())

    def __init__(self, player, collar, active=False):
        self.player = player
        self.player_name = player.name
        self.collar = collar
        self.active = active
        self.grace_until = utcnow() + timedelta(minutes=5)

    @classmethod
    def available_entries(cls):
        """ return all active Entries that are out of grace period """
        active_entries = Entry.query.filter(Entry.active == True)
        victims = []
        for ae in active_entries:
            if ae.grace_until < datetime.utcnow():
                victims.append(ae)
        return victims

    @classmethod
    def collar_active(cls, collar):
        e = Entry.query.filter(Entry.collar == collar, Entry.active == True).first() 
        if e:
            return True
        return False

    @classmethod
    def collar_player(cls, collar):
        e = Entry.query.filter(Entry.collar == collar, Entry.active == True).first() 
        if e:
            return e.player_name
        return False


class Game(Base):
    """ A game in the system. """
    __tablename__ = 'game'

    name = db.Column(db.String())
    num_players = db.Column(db.Integer())
    active = db.Column(db.Boolean)

    def __init__(self, name, num_players):
        self.name = name
        self.num_players = int(num_players)
        self.active = False

class Spin(Base):
    """ A game name and a string listing entry ids """
    __tablename__ = 'spin'

    game_name = db.Column(db.String())
    entries = db.Column(db.String())

    def __init__(self, game_name, entries):
        self.game_name = game_name
        self.entries = entries


