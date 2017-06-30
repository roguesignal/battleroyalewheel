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

