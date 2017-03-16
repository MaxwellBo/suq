__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
from os.path import abspath, join
from typing import *

# Libraries
from urllib.parse import urlparse
from flask import Flask, flash, jsonify, request, render_template, session, \
        redirect, url_for, send_from_directory, json # type: ignore
from werkzeug.utils import secure_filename
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_migrate import Migrate
# Imports
from suq.responses import *
from suq.models import *
import logging
from functools import wraps
import requests

### GLOBALS ###

app = Flask(__name__, static_folder="dep/suq_frontend/static", template_folder="dep/suq_frontend/templates")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in"
login_manager.login_message_category = "info"
UPLOAD_FOLDER = abspath('uploads/') # TODO: Make this folder if it doesn't exist
ALLOWED_EXTENSIONS = set(['ics'])
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')
engine = create_engine('sqlite://', echo=False)

### BINDINGS ###

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue


app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config["SECRET_KEY"] = "ITSASECRET"
app.config['SESSION_TYPE'] = 'filesystem'

db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    logging.warning("Resetting DB")
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
    return User.query.get(int(id))

def allowed_file(filename: str):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

### ENDPOINTS ###

@app.route('/', methods=['GET'])
def index():
    return app.send_static_file("index.html") # serves "dep/suq_frontend/index.html"

"""
    If a user is not logged in already, they can log in via FB or the form.
    If they log in via the form it hashes their password and checks it against the db
    If they log in via Facebook it runs a frontend fb sdk script. When they log in via that,
    it calls API_FB_Login, this will either log them in or make them a new user
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = session.get('user_id')

    if request.method == 'GET':
        return render_template("login.html")

    if (current_user.is_authenticated and query_user(user_id)) or query_FBuser(user_id):
        return redirect(url_for('profile'))

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
@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.filter_by(FBuserID=user_id).first()
    if user:
        if user.UserName == None:
            data = requests.get(
                "https://graph.facebook.com/me?fields=id,name,email&access_token=" + user.FBAccessToken)
            if data.status_code == 200:
                user.UserName = data.json()['name']
                db.session.add(user)
                db.session.commit()
                FBuser = data.json()['name']
        else:
            FBuser = user.UserName
    else:
        FBuser = ""

    return render_template("profile.html", FBuser=FBuser)

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
    accessToken = request.json['accessToken']
    existingUser = User.query.filter_by(FBuserID=userID).first()
    if existingUser == None:
        logging.warning("not a user, Creating new user")
        newUser = User(username=None, password=None, email=None, FBuserID=userID, FBAccessToken=accessToken)
        db.session.add(newUser) 
        db.session.commit()
        logging.warning("User made, userID = %s, accessToken = %s " % (userID, accessToken))
        login_user(newUser, remember=True)
        logging.warning("user is now logged in")
    else:
        logging.warning("User already exists :)")
        existingUser.FBAccessToken = accessToken
        existingUser.id = existingUser.FBuserID
        login_user(existingUser, remember=True)
    db.session.commit()
    return "logged_in"

"""
    Logs a user out...
"""
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route("/settings")
@login_required
def settings():
    return app.send_static_file("settings.html")

@app.route("/ok", methods=['GET'])
def result():
    return ok(["Here's", "your", "stuff"])

@app.route("/created", methods=['POST'])
def created_endpoint():
    return created(["I", "made", "this"])

@app.route("/error", methods=['GET'])
def error():
    raise InternalServerError(message="I made something break")

# http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'GET':
        raise NotImplemented(message="TODO")

    else:
        # check if the post request has a file part
        if 'file' not in request.files:
            raise BadRequest(message="No file part")

        file = request.files['file']

        # check if an empty file was sent
        if file.filename == '':
            raise BadRequest(message="No file was selected")

        if not allowed_file(file.filename):
            raise Forbidden(message="Filetype not permitted")

        if file:
            data = file.read()
            # http://werkzeug.pocoo.org/docs/0.11/datastructures/#werkzeug.datastructures.FileStorage.save
            caldb = CalDB(request.form['calname'], data)
            db.session.add(caldb)
            db.session.commit()
            return redirect(url_for('index'))


@app.route('/calendars', methods=['get'])
def viewcals():
    return render_template('calendars.html', calendars=CalDB.query.all())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
