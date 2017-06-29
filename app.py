from flask import Flask
from flask import render_template
from logging import handlers

app = Flask(__name__)
app.config.from_object('config')

## configure jinja2 environment
if not app.debug:
    import logging
    loghandler = logging.handlers.SysLogHandler(address='/dev/log')
    loghandler.setLevel(logging.WARNING)
    app.logger.addHandler(loghandler)

app.jinja_env.add_extension('jinja2.ext.do')

## set up csrf protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
csrf.init_app(app)

## init SQLAlchemy
from models import db
db.init_app(app)

#### endpoints and websockets
from flask import abort
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

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
        socketio.emit('refresh', {'message': 'test' + str(count)}, namespace='/leader')

@socketio.on('connect')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect')
def test_disconnect():
    print('client disconnected')

## web routes
@app.route('/entry', methods=['GET','POST'])
def entry():
    #form = LoginForm(request.form)
    #if request.method == 'POST':
    #    if form.validate_on_submit(): # auths against db
    #        route = request.access_route + [request.remote_addr]
    #        app.logger.info('LOGIN: ' + form.username.data + ' from route: ' + str(route))
    #        return redirect(request.args.get('next') or '/home')
    #    else:
    #        app.logger.warn('login failed for ' + form.username.data)

    return render_template('entry.html')

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

