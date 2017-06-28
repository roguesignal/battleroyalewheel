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
    visit_times = db.Column(JSON)
    competing = db.Column(db.Boolean)

    def __init__(self, name, wristband, collar):
        self.name = name 
        self.wristband = wristband
        self.collar = collar
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

class Entry(Base):
    """ Data related to a current player's active entry in the competition. """
    __tablename__ = 'entry'

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref=db.backref('entrys', lazy='dynamic')) 
    collar = db.Column(db.String())
    entrance_time = db.Column(db.DateTime())
    grace_until = db.Column(db.DateTime())
    num_plays = db.Column(db.Integer)

class Game(Base):
    """ A game in the system. """
    __tablename__ = 'game'

    name = db.Column(db.String())
    num_players = db.Column(db.Integer())
    active = db.Column(db.Boolean)
    


