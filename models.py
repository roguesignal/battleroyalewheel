from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class Base(db.Model, AbstractConcreteBase):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


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
        self.grace_until = db.func.now()

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

