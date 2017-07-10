#### endpoints and websockets
from flask import abort
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from app import app

from models import db
from models import Player
from models import Entry
from models import Game
from models import Spin

## TODO: player elapsed time
## TODO: report grace time to admin

## helper functions

import random

def spinthewheel():
    """ spin the wheel and add result to database """
    all_games = Game.query.filter(Game.active == True).all()
    available_entries = Entry.available_entries()
    possible_games = []
    for g in all_games:
        if g.num_players <= len(available_entries):
            possible_games.append(g)
    game = random.choice(possible_games)
    game_name = game.name
    entries = random.sample(available_entries, game.num_players)
    entry_ids = ""
    for e in entries:
        entry_ids += str(e.id) + ','
    entry_ids = entry_ids [:-1]
    spin = Spin(game_name, entry_ids)
    db.session.add(spin)
    db.session.commit
    # TODO: update grace_time
    # TODO: update num_plays
    # TODO: error catching
    return True

## websockets
from flask_socketio import SocketIO
from flask_socketio import emit
socketio = SocketIO(app)
thread = None

def background_thread():
    count = 0
    while True:
        socketio.sleep(1)
        count += 1
        # TODO: pull in live data here
        socketio.emit('refresh',
            {
                'message': 'test' + str(count),
                'leader': {'name': 'h@x0r5'},
                'toptimes': [ { 'name': 'bobross', 'time': '01h 55m 01s', 'dead': 'true'},
                    { 'name': 'lightningpants', 'time': '01h 20m 11s', 'dead': 'true'},
                    { 'name': 'h@xor5', 'time': '40m 31s', 'dead': 'false'},
                    { 'name': 'frodobaggins', 'time': '12m 44s', 'dead': 'true'},
                ],
                'showwheel': 'placeholder',
            },
            namespace='/leader')


@socketio.on('connect')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect')
def test_disconnect():
    print('client disconnected')

from forms import NewEntryForm
from forms import ReturnEntryForm
from forms import ExitForm
from forms import NewGameForm

## web routes
@app.route('/', methods=['GET'])
def index():
    return redirect('/entry')

@app.route('/entry', methods=['GET','POST'])
def entry():
    nef = NewEntryForm({})     # clear so we can have two forms with the same fieldnames here
    ref = ReturnEntryForm({})  # ""
    if request.method == 'POST':
        goingwell = True
        if 'register' in request.form:
            nef = NewEntryForm(request.form)
            if nef.validate_on_submit(): # validation checks for name + wristband uniqueness
                app.logger.info('creating new entry for: ' + nef.playername.data)
                try:
                    player = Player(nef.playername.data, nef.wristband.data)
                except Exception as e:
                    app.logger.error('newplayer failed: ' + str(e))
                    flash('FAILED NEW PLAYER PLAYER CREATE')
                    goingwell = False
                if goingwell:
                    try:
                        # create a new entry
                        entry = Entry(player, nef.collarid.data, active=True)
                    except Exception as e:
                        app.logger.error('entry creation failed: ' + str(e))
                        flash('FAILED NEW PLAYER ENTRY CREATE')
                        goingwell = False
                if goingwell:
                    try:
                        db.session.add(player)
                        db.session.add(entry)
                        db.session.commit()
                        flash('NEW PLAYER ' + nef.playername.data + ' ENTERED')
                    except Exception as e:
                        app.logger.error('db commit failed: ' + str(e))
                        flash('DATABASE IS HORKED')
            else:
                # did not validate, show errors
                app.logger.info('new entry form errors: ' + str(nef.errors))
                app.logger.warn('new entry failed for: ' + nef.playername.data)
                flash('FAILED TO ENTER NEW PLAYER')
        elif 'return' in request.form:
            ref = ReturnEntryForm(request.form)
            if ref.validate_on_submit(): # validation checks to make sure wristband exists, etc
                player = Player.query.filter(Player.wristband == ref.wristband.data).one_or_none()
                if player:
                    try:
                        entry = Entry(player, ref.collarid.data, active=True)
                        db.session.add(entry)
                        db.session.commit()
                    except Exception as e:
                        app.logger.error('entry creation failed: ' + str(e))
                        flash('SOMETHING HORKED WITH ENTRY CREATION')
                        goingwell = False
                else: 
                    flash('NO PLAYER WITH THAT WRISTBAND: ' + ref.wristband.data)
                    goingwell = False
            else:
                flash('PLAYER RETURN FAILED')
        else:
            abort(400)
    return render_template('entry.html', nef=nef, ref=ref)

@app.route('/exit', methods=['GET', 'POST'])
def exitplayer():
    ef = ExitForm(request.form)
    if request.method == 'POST':
        if ef.validate_on_submit():
            try:
                app.logger.info('exiting wristband ' + ef.wristband.data)
                p = Player.player_wristband(ef.wristband.data)
                entry = p.active_entry()
                entry.active = False
                entry.exit_time = db.func.now()
                p.num_exits += 1
                # TODO: update total player time played
                db.session.commit()
                flash('EXIT SUCCESSFUL')
            except Exception as e:
                flash('SOMETHING HORKED ON EXIT')
                app.logger.error('error on exit: ' + str(e))
        else:
            app.logger.error(ef)
            flash('INVALID EXIT SUBMISSION')

    return render_template('exit.html', ef=ef)

@app.route('/spin', methods=['GET', 'POST'])
def spin():
    if request.method == 'POST':
        spinthewheel()

    spins = Spin.query.order_by('id').all()
    if spins:
        most_recent_spin = spins[-1]
        game = most_recent_spin.game_name
        collars = []
        for ent in most_recent_spin.entries.split(','):
            e = Entry.query.filter(Entry.id == ent).one_or_none()
            collars.append(e.collar)
    else:
        game = 'none'
        collars = ['N/A']

    return render_template('spin.html', game=game, collars=collars)

from datetime import datetime

@app.route('/players', methods=['GET'])
def players():
    players = Player.query.all()
    playersl = []

    for p in players:
        pd = {}
        pd['name'] = p.name
        pd['wrist'] = p.wristband
        active_entry = p.active_entry()
        pd['collar'] = active_entry.collar if active_entry else 'DEAD'
        pd['grace'] = active_entry.grace_until if active_entry else '----'
        playersl.append(pd)
        now = datetime.utcnow()

    return render_template('players.html', players=playersl, now=now)

@app.route('/games', methods=['GET', 'POST'])
def games():
    if request.method == 'POST':
        ngf = NewGameForm(request.form)
        if 'newgame' in request.form:
            if ngf.validate_on_submit():
                newgame = Game(ngf.name.data, ngf.num_players.data)
                db.session.add(newgame)
                db.session.commit()
                ngf = NewGameForm({})
            else:
                flash('FAILED TO ADD NEW GAME')
        else:
            abort(400)
    else:
        ngf = NewGameForm({})

    games = Game.query.all()
    gamesl = []

    for g in games:
        gd = {}
        gd['id'] = g.id
        gd['name'] = g.name
        gd['players'] = g.num_players
        gd['active'] = g.active
        gamesl.append(gd)

    gamesl = sorted(gamesl, key=lambda k: k['name'])

    return render_template('games.html', games=gamesl, ngf=ngf)

@app.route('/disablegame/<id>', methods=['GET'])
def disablegame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    game.active = False
    db.session.commit()
    return redirect('/games')

@app.route('/activategame/<id>', methods=['GET'])
def activategame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    game.active = True
    db.session.commit()
    return redirect('/games')

@app.route('/deletegame/<id>', methods=['GET'])
def deletegame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    db.session.delete(game)
    db.session.commit()
    return redirect('/games')

@app.route('/leader', methods=['GET'])
def example(id):
    return render_template('leader.html')

import os

@app.route('/session', methods=['GET', 'POST'])
def session_access():
    if request.method == 'GET':
        return jsonify({
            'session': str(os.urandom(16)),
        })
    return '', 204

if __name__ == '__main__':
    socketio.run(app)

