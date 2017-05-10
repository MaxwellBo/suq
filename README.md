# SyncUQ

### Description

TODO

### Requirements

- Python 3.6
- Docker
- Heroku

### Configuration

#### Setting up the Python Sandbox

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip3 install -r ./requirements.txt`

#### Configuring the environment

- `export FLASK_DEBUG=1`
- `export FLASK_APP=app.py`

#### Configuring the Database

- `docker run --name suq_db -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:9.6.2`

### Development

#### Usage

- `./run.sh` to compile the frontend and boot a development Flask instance, not using Gunicorn

#### Precommit

To typecheck:

- `mypy run.py`

### Links

- [Type reference](https://docs.python.org/3/library/typing.html)
