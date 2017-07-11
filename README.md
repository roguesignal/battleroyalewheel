# royalewheel
royale with wheel

## dev environment setup (os x)

### install postgres and set up database
https://www.postgresql.org/download/macosx/

> psql
> create database brw;

### homebrew, python3, git
> /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
> brew install python3 git

### clone this repo and set up the virtual env
> git clone https://github.com/trammellventures/royalewheel
> cd royalewheel
> pyvenv venv
> source venv/activate/bin
> pip install -r requirements.txt

note that `source venv/activate/bin` loads the virtual environment and needs to
be run prior to running the webapp

### create flask environment

define the following environment variables in your .bash_profile or with autoenv:

    export BRW_ENVIRONMENT=development
    export BRW_DATABASE_URL=postgres://<username>@localhost:5432/brw
    export BRW_SECRET_KEY='GIBBERISH_HERE'

### populate database

> python manage.py db upgrade

### run the app

> source venv/bin/activate
> python wheel.py

browse to localhost:5000

### how to update the codebase + database with git

> git pull origin
> pip install -r requirements.txt
> python manage.py db upgrade

