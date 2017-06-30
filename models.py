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
    
    name = db.Column(db.String())
    wristband = db.Column(db.String())
    total_time_played = db.Column(db.DateTime())
    num_exits = db.Column(db.Integer())

    def __init__(self, name, wristband):
        self.name = name 
        self.wristband = wristband
        self.total_time_played = 0
        self.last_entry_time = db.func.now()
        self.competing = True

    def __repr__(self):
        return '<Player {}>'.format(self.name)

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


class Entry(Base):
    """ Data related to a player's entry in the competition. """
    __tablename__ = 'entry'

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref=db.backref('entry', lazy='dynamic')) 
    exit_time = db.Column(db.DateTime())
    grace_until = db.Column(db.DateTime())
    num_plays = db.Column(db.Integer)
    active = db.Column(db.Boolean)

    def __init__(self, player):
        self.player_id = player.id
        self.player = player
        self.grace_until = db.func.now()


class Collar(Base):
    """ """
    __tablename__ = 'collar'
    collar_id = db.Column(db.String)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    entry = db.relationship('Entry', backref=db.backref('collar', lazy='dynamic'))

class Game(Base):
    """ A game in the system. """
    __tablename__ = 'game'

    name = db.Column(db.String())
    num_players = db.Column(db.Integer())
    active = db.Column(db.Boolean)

