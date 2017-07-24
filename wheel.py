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

import random
from datetime import datetime
from datetime import timedelta

## helper functions
def hhmmss(sec):
    """ returns hours, minutes, and seconds from seconds """
    # TODO: add a handler for 'days' for long games
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return "%dh %02dm %02ds" % (h, m, s)
    return "%dm %02ds" % (m, s)

def spinthewheel():
    """ spin the wheel and add result to database """
    all_games = Game.query.filter(Game.active == True).all()
    available_entries = Entry.available_entries()
    possible_games = []
    for g in all_games:
        if g.num_players <= len(available_entries):
            possible_games.append(g)
    if len(possible_games) < 1:
        return False
    game = random.choice(possible_games)
    game_name = game.name
    entries = random.sample(available_entries, game.num_players)
    entry_ids = ""
    for e in entries:
        e.add_grace_minutes(5)
        entry_ids += str(e.id) + ','
    entry_ids = entry_ids[:-1]
    spin = Spin(game_name, entry_ids)
    db.session.add(spin)
    db.session.commit()
    # TODO: error catching
    return True

## websockets
from flask_socketio import SocketIO
from flask_socketio import emit
socketio = SocketIO(app)
thread = None

def background_thread():
    """ manages the leaderboard and wheel spin for the websockets """

    # import the app context
    ctx = app.test_request_context()
    ctx.push()

    while True:
        socketio.sleep(1)

        toptimes = []
        players = Player.query.all()
        for p in players:
            dead = 'true'
            entries = Entry.query.filter(Entry.player_name == p.name).all()
            elapsed_time = timedelta(0)
            for e in entries:
                if e.active:
                    dead = 'false'
                    elapsed_time += (datetime.utcnow() - e.created_on)
                else:
                    elapsed_time += (e.exit_time - e.created_on) # bad timezones
            toptimes.append({'name': p.name, 'time': elapsed_time, 'dead': dead})
        
        # order toptimes by elapsed_time
        toptimes = sorted(toptimes, key=lambda k: k['time'], reverse=True)
        toptimes = [{'name': t['name'], 'time': hhmmss(t['time'].seconds), 'dead': t['dead']} for t in toptimes]

        # leader is top time elapsed + still alive
        leader = 'nobody'
        for tt in toptimes:
            if tt['dead'] == 'false':
                leader = tt['name']
                break

        # latest spin, checks to see if recent with recent_spin()
        spins = Spin.query.order_by('id').all()
        if spins and len(spins) > 0:
            latest_spin = spins[-1]
            game_name = latest_spin.game_name
            spin_players = " | ".join(latest_spin.spin_players())
            if latest_spin:
                spin_state = latest_spin.spin_state()
            else:
                spin_state = 'leaderboard'
        else:
            game_name = 'WAIT FOR IT'
            spin_players = ''
            spin_state = 'leaderboard'

        if spin_state != 'leaderboard':
            show_spin = True
        else:
            show_spin = False

        # elapsed time
        first_entry = Entry.query.order_by('id').first()
        if first_entry:
            game_elapsed = hhmmss((datetime.utcnow() - first_entry.created_on).seconds)
        else:
            game_elapsed = 'NO ENTRANTS YET'

        socketio.emit('refresh',
            {
                'leader': {'name': leader},
                'toptimes': toptimes,
                'showwheel': 'placeholder',
                'spin': {
                    'show': show_spin,
                    'game': game_name,
                    'players': spin_players,
                    'state': spin_state
                },
                'gametime': game_elapsed,
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
    app.logger.warn('client disconnected')

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
                        nef = NewEntryForm({})
                    except Exception as e:
                        app.logger.error('db commit failed: ' + str(e))
                        flash('DATABASE IS HORKED')
            else:
                # did not validate, show errors
                app.logger.debug('new entry form errors: ' + str(nef.errors))
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
                        playername = Player.player_wristband(ref.wristband.data).name
                        flash('RETURNING PLAYER ' + playername + ' ENTERED')
                        ref = ReturnEntryForm({})
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
                if ef.wristband.data and ef.wristband.data != "":
                    app.logger.info('exiting wristband ' + ef.wristband.data)
                    p = Player.player_wristband(ef.wristband.data)
                else:
                    app.logger.info('exiting collar ' + ef.collarid.data)
                    pname = Entry.active_collar_playername(ef.collarid.data)
                    p = Player.query.filter(Player.name == pname).one_or_none()
                p.num_exits += 1
                entry = p.active_entry()
                entry.exit_player()
                db.session.commit()
                flash('EXIT SUCCESSFUL - ' + str(p.name) + ' | ' + str(p.wristband) + ' | ' + str(entry.collar))
                ef = ExitForm({})
            except Exception as e:
                flash('SOMETHING HORKED ON EXIT')
                app.logger.error('error on exit: ' + str(e))
        else:
            app.logger.error(ef)
            flash('INVALID EXIT SUBMISSION')

    return render_template('exit.html', ef=ef)

@app.route('/spin', methods=['GET', 'POST'])
def spin():
    spinerror = False
    if request.method == 'POST':
        spinerror = not spinthewheel()

    spins = Spin.query.order_by('id').all()
    history = []
    for s in spins:
        hist = {}
        hist['game'] = s.game_name
        entries = [ Entry.query.filter(Entry.id == ent).one_or_none() for ent in s.entries.split(',') ] 
        hist['collars'] = [ e.collar for e in entries ]
        hist['timestamp'] = str(s.created_on).split()[1][:-7]
        history.append(hist)

    if not spins:
        history.append({'game': 'none', 'collars': ['N/A']})

    history = history[::-1]
    return render_template('spin.html', history=history, spinerror=spinerror)

@app.route('/players', methods=['GET'])
def players():
    players = Player.query.all()
    playersl = []

    for p in players:
        pd = {}
        pd['name'] = p.name
        pd['wrist'] = p.wristband
        active_entry = p.active_entry()
        pd['collar'] = active_entry.collar if active_entry else '----'
        pd['grace'] = str(active_entry.grace_until)[:-7] if active_entry and active_entry.grace_until > datetime.utcnow() else '----'
        playersl.append(pd)

    now = str(datetime.utcnow())[:-7]
    return render_template('players.html', players=playersl, now=now)

@app.route('/config', methods=['GET', 'POST'])
def config():
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
    return render_template('config.html', games=gamesl, ngf=ngf)

@app.route('/disablegame/<id>', methods=['GET'])
def disablegame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    game.active = False
    db.session.commit()
    return redirect('/config')

@app.route('/activategame/<id>', methods=['GET'])
def activategame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    game.active = True
    db.session.commit()
    return redirect('/config')

@app.route('/deletegame/<id>', methods=['GET'])
def deletegame(id):
    game = Game.query.filter(Game.id == id).one_or_none()
    db.session.delete(game)
    db.session.commit()
    return redirect('/config')

@app.route('/leader', methods=['GET'])
def leaderboard():
    return render_template('leader.html')

@app.route('/reset', methods=['POST'])
def reset_players():
    if 'reset_players' in request.form:
        Spin.query.delete()
        Entry.query.delete()
        Player.query.delete()
        db.session.commit()
    elif 'reset_spins' in request.form:
        Spin.query.delete()
        db.session.commit()
    else:
        app.logger.info.warn('called reset without proper button')
    return redirect('/config')

import os

@app.route('/session', methods=['GET', 'POST'])
def session_access():
    if request.method == 'GET':
        return jsonify({
            'session': str(os.urandom(16)),
        })
    return '', 204

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')

