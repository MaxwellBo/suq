# suq_backend

### Requirements

- Python 3.6
- Docker

### Setup Unix

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip3 install -r ./requirements.txt`
- `export FLASK_DEBUG=1`
- `export FLASK_APP=./suq/__init__.py`

### Setup Windows

- `python -m venv .venv`
- `.venv\Scripts\activate.bat`
- `pip3 install -r .\requirements.txt`
- `set FLASK_DEBUG=1`
- `set FLASK_APP=.\suq\__init__.py`

### Usage

- `flask run`

### Development

To typecheck:

- `mypy run.py`

### Links

- [Type reference](https://docs.python.org/3/library/typing.html)
