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
        if p:
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
    active = db.Column(db.Boolean)   # TODO: redundant with exit_time
    collar = db.Column(db.String())

    def __init__(self, player, collar, active=False):
        self.player = player
        self.player_name = player.name
        self.collar = collar
        self.active = active
        self.grace_until = utcnow() + timedelta(minutes=5)

    def add_grace_minutes(self, minutes):
        self.grace_until = utcnow() + timedelta(minutes=minutes)
        db.session.commit()

    def exit_player(self):
        self.active = False
        self.exit_time = utcnow()
        db.session.commit()

    @classmethod
    def available_entries(cls):
        """ return all active Entries that are out of grace period """
        """ checks if Config is obeying grace periods or not """
        active_entries = Entry.query.filter(Entry.active == True)
        victims = []
        obey_grace = Config.get_config().obey_grace
        for ae in active_entries:
            if not obey_grace or ae.grace_until < datetime.utcnow():
                victims.append(ae)
        return victims

    @classmethod
    def collar_active(cls, collar):
        e = Entry.query.filter(Entry.collar == collar, Entry.active == True).first() 
        if e:
            return True
        return False

    @classmethod
    def active_collar_playername(cls, collar):
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
        self.active = True


class Spin(Base):
    """ A game name and a string listing entry ids """
    __tablename__ = 'spin'

    game_name = db.Column(db.String())
    entries = db.Column(db.String())

    def __init__(self, game_name, entries):
        self.game_name = game_name
        self.entries = entries

    def spin_collars(self):
        entries = [ Entry.query.filter(Entry.id == ent).one_or_none() for ent in self.entries.split(',') ]
        collars = [ e.collar for e in entries ]
        return collars

    def spin_players(self):
        entries = [ Entry.query.filter(Entry.id == ent).one_or_none() for ent in self.entries.split(',') ]
        players = [ (e.player_name, e.collar) for e in entries ]
        return players

    def spin_state(self):
        if self.created_on + timedelta(seconds=3) > datetime.utcnow():  
            return 'wheel'
        elif self.created_on + timedelta(seconds=5) > datetime.utcnow():  
            return 'of'
        elif self.created_on + timedelta(seconds=7) > datetime.utcnow():  
            return 'death'
        elif self.created_on + timedelta(seconds=13) > datetime.utcnow():  
            return 'spinner'
        elif self.created_on + timedelta(seconds=50) > datetime.utcnow():  
            return 'results'
        return 'leaderboard'

class Config(Base):
    """ Current config options. """
    __tablename__ = 'config'

    obey_grace = db.Column(db.Boolean())

    def __init__(self):
        self.obey_grace = True

    @classmethod
    def get_config(cls):
        config_l = Config.query.all()
        if len(config_l) == 0:
            config = Config()
            db.session.add(config)
            db.session.commit()
        else:
            config = config_l[0]

        return config



