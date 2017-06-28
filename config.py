import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = os.environ['BRW_SECRET_KEY'] 
ENVIRONMENT = os.environ['BRW_ENVIRONMENT']
DEBUG = (ENVIRONMENT == 'development')
TESTING = (ENVIRONMENT == 'development')

SQLALCHEMY_DATABASE_URI = os.environ['BRW_DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
