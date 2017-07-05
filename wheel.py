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
        # socketio.emit('refresh', {'message': 'test' + str(count)}, namespace='/leader')
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

## web routes
@app.route('/entry', methods=['GET'])
def entry():
    nef = NewEntryForm()
    ref = ReturnEntryForm()
    return render_template('entry.html', nef=nef, ref=ref)

@app.route('/newplayer', methods=['POST'])
def newplayer():
    nef = NewEntryForm()
    if nef.validate_on_submit():
        goingwell = True
        app.logger.info('new entry for: ' + nef.playername)
        try:
            player = Player(nef.playername.data, nef.wristband.data)
            db.session.add(player)
            db.session.commit()
        except Exception as e:
            app.logger.error('newplayer failed: ' + str(e))
            flash('FAILED NEW PLAYER ENTRY - DB IS HORKED')
            goingwell = False
        if goingwell:
            try:
                entry = Entry(nef.playername.data, nef.wristband.data)
                db.session.add(p)
                db.session.commit()
            except Exception as e:
                app.logger.error('entry creation failed: ' + str(e))
                flash('FAILED NEW PLAYER ENTRY - DB IS HORKED')
                goingwell = False
        flash('NEW PLAYER ENTERED')
        # add Entry to db
        # associate Collar with Entry
        # db commit
    else:
        app.logger.warn('new entry failed for: ' + nef.playername)
        flash('FAILED TO ENTER NEW PLAYER')
    return redirect('/entry')

@app.route('/returnplayer', methods=['POST'])
def returnplayer():
    ref = ReturnEntryForm()
    if ref.validate_on_submit():
        app.logger.info('return entry for: ' + ref.playername)
        flash('RETURNING PLAYER ENTERED')
    else:
        app.logger.warn('returning entry failed for: ' + ref.playername)
        flash('FAILED TO ENTER RETURNING PLAYER')
    return redirect('/entry')

@app.route('/exit', methods=['GET, POST'])
def exitplayer():
    return render_template('exit.html')

@app.route('/spin', methods=['GET, POST'])
def spinthewheel():
    return render_template('spin.html')

@app.route('/players', methods=['GET, POST'])
def players():
    return render_template('players.html')

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

