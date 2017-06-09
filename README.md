# [SyncUQ](https://www.syncuq.com)
![Mobile app mockups](/docs/app_layout.jpg)



SyncUQ aims to be the first University of Queensland exclusive schedule sharing platform. Users will be able to share their timetables with friends and get live updates of when their friends are free. It also has the bonus functionality of allowing users to plan meetings with one another.
### Demo
[syncuq.com](https://www.syncuq.com)

### Requirements

- Python 3.6
- Docker
- Heroku
- Ruby

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

#### Downloading development dependencies

- `sudo gem install sass`

### Development

#### Usage

- `./run.sh` to compile the frontend and boot a development Flask instance, not using Gunicorn

#### Migrate DB
To migrate the db, all you have to do is make changes like you normal would to the models.py file.
Then run
- `flask db migrate` to generate a migration file
and
- `flask db upgrade` to change the db to the new schema

now the db should be properly formatted and work.

#### Migrate DB server side
Run 
- `heroku run bash --app syncuq-stage` to get into bash on heroku

then inside bash
- `export FLASK_APP=app.py`

then, assuming you have pushed the migrations file created from migrating locally, just run 
this command to get the server side db to upgrade
- `flask db upgrade` 

if something goes wrong, there is a good chance you can fix it by running the following
- `rm -r migrations` delete the migrations folder
- `flask db init` remake the migrations folder
- `flask db migrate` create the migration
- `flask db upgrade` perform the migration
#### Precommit

To typecheck:

- `mypy run.py`

### Links

- [Type reference](https://docs.python.org/3/library/typing.html)
