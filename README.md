# suq_backend

### Requirements

- Python 3.6
- Docker

### Setup

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip3 install -r ./requirements.txt`
- `export FLASK_DEBUG=1`
- `export FLASK_APP=./suq/__init__.py`

#### DB

- Create: `docker run --name suq_db -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:9.6.2`
- Configure: `psql -h localhost -p 5432 --username=postgres`
- Halt: `docker stop suq_db`
- Restart: `docker restart suq_db`
- Delete: `docker rm suq_db`

### Usage

- `flask run`

### Development

To typecheck:

- `mypy run.py`

### Links

- [Type reference](https://docs.python.org/3/library/typing.html)
