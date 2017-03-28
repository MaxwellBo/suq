__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
from os.path import abspath, join
from functools import wraps
from typing import *

# Libraries
from urllib.parse import urlparse
from flask import Flask, flash, jsonify, request, render_template, session, \
        redirect, url_for, send_from_directory, json # type: ignore
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_migrate import Migrate
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
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')
engine = create_engine('sqlite://', echo=False)

### BINDINGS ###

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue


app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config["SECRET_KEY"] = "ITSASECRET"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
"""
migrate = Migrate(app, db)
"""
with app.app_context():
    logging.warning("Resetting DB")
    #HasFriend.__table__.drop(engine)
    db.create_all()
    db.session.commit()
    logging.debug("DB reset")

def to_json(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        get_fun = func(*args, **kwargs)
        return json.dumps(get_fun)

    return wrapper
# Finds whether user is already registered
def query_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    return False

# Finds whether a facebook user has logged in before
def query_FBuser(FBuserID):
    FBuser = User.query.filter_by(FBuserID=FBuserID).first()
    if FBuser:
        return True
    return False

def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')

# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error):
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

### UTILS ###

@login_manager.user_loader
def load_user(id):
    if id == None:
        return None
    try:
        user = User.query.get(int(id))
    except:
        return None
    return user

@app.after_request
def add_header(response):
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
def frontend():
    return app.send_static_file("app.html")


@app.route('/', methods=['GET'])
def index():
    return app.send_static_file("index.html")

"""
    If a user is not logged in already, they can log in via FB or the form.
    If they log in via the form it hashes their password and checks it against the db
    If they log in via Facebook it runs a frontend fb sdk script. When they log in via that,
    it calls API_FB_Login, this will either log them in or make them a new user
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
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
    pw_form = User.psw_to_md5(request.form['password'])
    pw_db = user.password
    if pw_form == pw_db:
        login_user(user, remember=True)
        flash('Logged in successfully')
        return redirect(url_for('profile'))
    return render_template("login.html", error="username or password error")

"""
    For people who want to register the old fashioned way.
"""
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    newAccount = User(username=username, password=password, email=email, FBuserID="", FBAccessToken="")
    db.session.add(newAccount)
    db.session.commit()
    return redirect(url_for("profile"))

"""
    This page will only show if a user has logged in, otherwise it redirects to login page
"""
@app.route('/samplecal')
@login_required
def sample_cal():
    events = get_test_calendar_events()
    todaysDate = datetime.now(timezone(timedelta(hours=10)))
    events = get_this_weeks_events(todaysDate, events)
    eventsDict = weeks_events_to_dictionary(events)
    return json.dumps(eventsDict)

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    name = current_user.username
    profilepicURL = current_user.profilePicture
    email = current_user.email
    calendarURL = current_user.calendarURL
    return ok({"name":name, "dp":profilepicURL, "email":email, "calURL":calendarURL})


@app.route('/calendar',  methods=['POST'])
@login_required
def calendar():
    calURL = request.json['url']
    current_user.calendarURL = calURL
    db.session.flush()
    db.session.commit()
    return created()

@app.route('/checkLogin')
@login_required
def callback():
    return redirect(redirect_url())

"""
    Finds whether a user exists on our system, returns vague '44' if they do not exist
    Not sure what this is used for, it is not currently used by our app
    May be useful in the future though.
"""
@app.route('/API_check_UserNameExist', methods=['POST'])
@to_json
def API_check_UserNameExist():
    username = request.json['username']
    user = User.query.filter_by(username=username).first()
    if user == None:
        return "44"
    return "logged_in"

"""
    Uses the JSON passed to us from the frontend to either 'log in' a user, or register them
    if they do not exist
"""
@app.route('/API_FB_login', methods=['POST'])
@to_json
def API_FB_login():
    logging.warning("FACEBOOK LOGIN DETECTED")
    userID = request.json['userID']
    existingUser = User.query.filter_by(FBuserID=userID).first()

    if existingUser == None:
        accessToken = request.json['accessToken']
        logging.warning("not a user, Creating new user")
        newUser = User(username=None, password=None, email=None, FBuserID=userID, FBAccessToken=accessToken)
        db.session.add(newUser)
        db.session.commit()
        logging.warning("User made, userID = %s, accessToken = %s " % (userID, accessToken))
        login_user(newUser, remember=True)
        logging.warning("user is now logged in")

    else:
        logging.warning("User already exists :)")
        try:
            username = request.json['userName']
            email = request.json['email']
            logging.warning("Updating user with name %s to %s" % (existingUser.username, username))
            logging.warning("Updating user with email %s to %s" % (existingUser.email, email))
            existingUser.username = username #incase they've changer their name on facebook since they registered
            existingUser.email = email #incase they've changed their email since they registered
        except KeyError:
            pass

        try:
            accessToken = request.json['accessToken']
            logging.warning("adding new accessToken")
            existingUser.FBAccessToken = accessToken #update their accessToken with the one supplied
        except KeyError:
            pass
        logging.warning("LOGGING IN USER")    
        login_user(existingUser, remember=True)
        logging.warning("User logged in :)")    
    db.session.flush()
    db.session.commit()
    return "Logged In! Please redirect me to app!"

"""
    Logs a user out...
"""
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/settings")
@login_required
def settings():
    return app.send_static_file("settings.html")

@app.route("/ok", methods=['GET'])
def result():
    return ok(["Here's", "your", "stuff"])

@app.route("/okauth", methods=['GET'])
@login_required
def resultAuth():
    return ok(["Here's", "your", "private", "stuff"])

@app.route("/created", methods=['POST'])
def created_endpoint():
    return created(["I", "made", "this"])

@app.route("/error", methods=['GET'])
def error():
    raise InternalServerError(message="I made something break")

if __name__ == '__main__':
    logging.warning("running app")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
