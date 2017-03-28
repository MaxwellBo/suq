# suq_backend

### Requirements

- Python 3.6
- Docker

### Setup Unix

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip3 install -r ./requirements.txt`
- `export FLASK_DEBUG=1`
- `export FLASK_APP=app.py`

### Setup Windows

- `python -m venv .venv`
- `.venv\Scripts\activate.bat`
- `pip3 install -r .\requirements.txt`
- `set FLASK_DEBUG=1`
- `set FLASK_APP=app.py`

#### DB

- Create: `docker run --name suq_db -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:9.6.2`
- Configure: `psql -h localhost -p 5432 --username=postgres`
- Halt: `docker stop suq_db`
- Restart: `docker restart suq_db`
- Delete: `docker rm suq_db`

### Heroku DB setup

http://blog.y3xz.com/blog/2012/08/16/flask-and-postgresql-on-heroku

If for some reason, the db isn't working on heroku, this might work
- Go to terminal, open up where suq is located
- type `heroku run python`
- once the python thingy is open
- type `from app import db`
- type `db.create_all()`

### Usage

- `flask run`

### Development

To typecheck:

- `mypy run.py`

### Links

- [Type reference](https://docs.python.org/3/library/typing.html)

- `elm-make src/Main.elm --output=static/app.html --yes`
