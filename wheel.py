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
    ef = ExitForm()
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

@app.route('/spin', methods=['GET, POST'])
def spinthewheel():
    # update grace_time
    # update num_plays
    return render_template('spin.html')

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
        playersl.append(pd)

    return render_template('players.html', players=playersl)

@app.route('/games', methods=['GET, POST'])
def games():
    return render_template('games.html')

@app.route('/leader', methods=['GET','POST'])
def example():
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

