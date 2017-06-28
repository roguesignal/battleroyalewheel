import hashlib
import io
import json
import random
import re
import string
from functools import wraps

from flask import abort
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from sqlalchemy.sql import func

from app import app # init all the things
from models import db

from models import Player
from models import Entry
from models import Game

#### ROUTES

## main homepage
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
