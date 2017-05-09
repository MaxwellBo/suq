__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
from os.path import abspath, join
from functools import wraps
from typing import *

# Libraries
from urllib.parse import urlparse
from flask import Flask, flash, jsonify, request, render_template, session, redirect, url_for, send_from_directory, json # type: ignore
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user # type: ignore
# Imports
from suq.responses import *
from suq.models import *
import logging
import requests

### GLOBALS ###

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in"
login_manager.login_message_category = "info"
# TODO: These look wrong
# TODO: Should we be using globals, or retrieving it from app.config
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')
engine = create_engine('sqlite://', echo=False) # type: ignore

### BINDINGS ###

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config["SECRET_KEY"] = "ITSASECRET"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

### GLOBALS ###

db.init_app(app)

### SETUP ###

with app.app_context():
    db.create_all()
    db.session.commit()

### HELPER FUNCTIONS ###

# TODO: Remove this to responses and type declare it
def to_json(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        get_fun = func(*args, **kwargs)
        return jsonify(get_fun)

    return wrapper

# Finds whether user is already registered
def query_user(username: str) -> bool:
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    return False

"""
Finds whether a facebook user has logged in before
"""
def query_fb_user(fb_user_id: str) -> bool:
    if User.query.filter_by(fb_user_id=fb_user_id).first():
        return True
    return False

def redirect_url() -> Response:
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')

# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error: Any) -> Any:
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

### UTILS ###

@login_manager.user_loader
def load_user(id: str) -> Any: #is this the right type?
    if id == None:
        return None
    try:
        user = User.query.get(int(id))
    except:
        return None
    return user

@app.after_request
def add_header(response: Response) -> Response:
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

### ENDPOINTS ###

@app.route('/app', methods=['GET'])
@login_required
def frontend() -> Response:
    return app.send_static_file("app.html")

@app.route('/whatsdue', methods=['GET','POST'])
def whatsdue() -> Response:
    if request.method == 'GET':
        return render_template("whatsdue.html")
    else:
        subjects = []
        subjects.append(request.form['subject1'])
        subjects.append(request.form['subject2'])
        subjects.append(request.form['subject3'])
        subjects.append(request.form['subject4'])
        subjects.append(request.form['subject5'])
        data = get_whats_due(subjects)
        return jsonify(data)

@app.route('/', methods=['GET'])
def index() -> Response:
    return app.send_static_file("index.html")

"""
If a user is not logged in already, they can log in via FB or the form.
If they log in via the form it hashes their password and checks it against the db
If they log in via Facebook it runs a frontend fb sdk script. When they log in via that,
it calls fb_login, this will either log them in or make them a new user
"""
@app.route('/login', methods=['GET', 'POST'])
def login() -> Response:
    if current_user.is_authenticated:
        logging.warning("User at login page is logged in")
    else:
        logging.warning("User at login page is not logged in")
    if request.method == 'GET':
        return render_template("login.html")
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user == None:
        return render_template("login.html", error="username or password error")
    if User.check_password(request.form['password']):
        login_user(user, remember=True)
        flash('Logged in successfully')
        return redirect(url_for('profile'))
    return render_template("login.html", error="username or password error")

"""
For people who want to register the old fashioned way.
"""
@app.route('/register', methods=['GET', 'POST'])
def register() -> Response:
    if request.method == 'GET':
        return render_template("register.html")
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    new_account = User(username=username, password=password, email=email, fb_user_id="", fb_access_token="")
    db.session.add(new_account)
    db.session.commit()
    return redirect(url_for("profile"))

"""
This page will only show if a user has logged in, otherwise it redirects to login page
"""
@app.route('/sample-cal')
@login_required
def sample_cal() -> Response:
    events = get_test_calendar_events()
    todays_date = datetime.now(BRISBANE_TIME_ZONE)
    events = get_this_weeks_events(todays_date, events)
    events_dict = weeks_events_to_dictionary(events)
    return json.dumps(events_dict)

@app.route('/weeks-events', methods=['GET'])
@login_required
def weeks_events() -> Response:
    if (current_user.calendar_data is None):
        return ok("Calendar not yet added!")
    user_calendar = load_calendar_from_data(current_user.calendar_data)
    user_events = get_events(user_calendar)
    todays_date = datetime.now(BRISBANE_TIME_ZONE)
    user_events = get_this_weeks_events(todays_date, user_events)
    events_dict = weeks_events_to_dictionary(user_events)
    return ok(events_dict)

@app.route('/profile', methods=['GET'])
@login_required
def profile() -> Response:
    name = current_user.username
    profile_pic_url = current_user.profile_picture
    email = current_user.email
    calendar_url = current_user.calendar_url
    return ok({"name":name, "dp":profile_pic_url, "email":email, "calURL":calendar_url})

# TODO: https://github.com/MaxwellBo/suq_backend/issues/8
@app.route('/all-users-info', methods=['GET'])
@login_required
def all_users_info() -> Response:
    list_of_all_users = User.query.all()
    logging.warning(list_of_all_users)
    all_user_info = []
    for user in list_of_all_users:
        all_user_info.append(get_user_status(user))
    return ok(all_user_info)

@app.route('/calendar',  methods=['POST'])
@login_required
def calendar() -> Response:
    cal_url = request.json['url']
    logging.warning(f"Recieved Cal {cal_url}")

    if (is_url_valid(cal_url) == False):
        raise InternalServerError(message="Invalid URL")

    if current_user.add_calendar(cal_url) == False:
        raise InternalServerError(message="Invalid Calendar")

    # FIXME: Use snake_case for these variable names
    user_calendar = load_calendar_from_data(current_user.calendar_data)
    user_events = get_events(user_calendar)
    todays_date = datetime.now(BRISBANE_TIME_ZONE)
    user_events = get_this_weeks_events(todays_date, user_events)
    events_dict = weeks_events_to_dictionary(user_events)
    logging.warning(str(events_dict))
    db.session.flush()
    db.session.commit()
    # FIXME: This should be
    logging.warning(f"CalUpdated {current_user.calendar_url}")
    return created("Calendar Successfully Added!")

@app.route('/check-login')
@login_required
def check_login() -> Response:
    return redirect(redirect_url())

"""
Finds whether a user exists on our system, returns vague '44' if they do not exist
Not sure what this is used for, it is not currently used by our app
May be useful in the future though.
"""
@app.route('/check-username-exists', methods=['POST'])
@to_json
def check_username_exists() -> Response:
    username = request.json['username']
    user = User.query.filter_by(username=username).first()
    if user is None:
        return "44" # TODO: Why is this 44?
    return "logged_in"

"""
Uses the JSON passed to us from the frontend to either 'log in' a user, or register them
if they do not exist
"""
@app.route('/fb-login', methods=['POST'])
@to_json
def fb_login() -> Response:
    logging.warning("FACEBOOK LOGIN DETECTED") # FIXME: More formal logging
    user_id = request.json['userID']
    existing_user = User.query.filter_by(fb_user_id=user_id).first()

    if existing_user is None:
        access_token = request.json['accessToken']
        logging.warning("Not a user, creating new user")
        new_user = User(username=None, password=None, email=None, fb_user_id=user_id, fb_access_token=access_token)
        db.session.add(new_user)
        db.session.commit()
        logging.warning(f"User made, user_id = {user_id}, access_token = {access_token}")
        login_user(new_user, remember=True)
        logging.warning("User is now logged in")

    else:
        logging.warning("User already exists")
        try:
            username = request.json['userName']
            email = request.json['email']
            logging.warning(f"Updating user with name {existing_user.username} to {username}")
            logging.warning(f"Updating user with email {existing_user.email} to {email}")
            existing_user.username = username #incase they've changer their name on facebook since they registered
            existing_user.email = email #incase they've changed their email since they registered
        except KeyError:
            pass

        try:
            access_token = request.json['accessToken']
            logging.warning("Adding new accessToken")
            existing_user.fb_access_token = access_token #update their accessToken with the one supplied
        except KeyError:
            pass
        logging.warning("Logging in user")
        login_user(existing_user, remember=True)
        logging.warning("User logged in")
    db.session.flush()
    db.session.commit()
    return "Logged In! Please redirect me to app!"

"""
Logs a user out...
"""
@app.route('/logout')
def logout() -> Response:
    logout_user()
    return redirect(url_for('login'))

@app.route("/settings")
@login_required
def settings() -> Response:
    return app.send_static_file("settings.html")

if __name__ == '__main__':
    logging.warning("Running app")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
