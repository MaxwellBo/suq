__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
from os.path import abspath, join
from typing import *

# Libraries
from urllib.parse import urlparse
from flask import Flask, flash, jsonify, request, render_template, session, \
        redirect, url_for, send_from_directory # type: ignore
from werkzeug.utils import secure_filename
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_migrate import Migrate
# Imports
from suq.responses import *
from suq.models import *
from flask_oauthlib.client import OAuth, OAuthException
import logging
### GLOBALS ###

app = Flask(__name__, static_folder="dep/suq_frontend/static")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
UPLOAD_FOLDER = abspath('uploads/') # TODO: Make this folder if it doesn't exist
ALLOWED_EXTENSIONS = set(['ics'])
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')


### BINDINGS ###

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue


app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config["SECRET_KEY"] = "ITSASECRET"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SOCIAL_FACEBOOK'] = {
    'consumer_key': '1091049127696748',
    'consumer_secret': 'ae6513c59a726ebd6158c7c5483e858c'
}
app.config['SECURITY_POST_LOGIN'] = '/profile'

oauth = OAuth(app)

facebook = oauth.remote_app(
    'facebook',
    consumer_key='1091049127696748',
    consumer_secret='ae6513c59a726ebd6158c7c5483e858c',
	request_token_params={'scope': 'email'},
	base_url='https://graph.facebook.com',
	request_token_url=None,
	access_token_url='/oauth/access_token',
	access_token_method='GET',
	authorize_url='https://www.facebook.com/dialog/oauth'
)


db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    logging.warning("Resetting DB")
    db.create_all()
    db.session.commit()
    logging.debug("DB reset")


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
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login')
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next')
            or request.referrer 
            or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


@app.route('/login/fb_authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message
 
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get(
        '/me/?fields=email,name,id,picture.height(200).width(200)'
    )
    return redirect(url_for('profile'))
 
@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')



"""
@app.route('/', methods=['GET'])
def index():
    return app.send_static_file("index.html") # serves "dep/suq_frontend/index.html"
"""

@app.route('/register' , methods=['GET','POST'])
def register():
    logging.warning("register route")
    #Form validation is to be done client side
    if request.method == 'GET':
        logging.warning("Get request, serving html")
        return app.send_static_file("register.html")
    logging.warning("form submit, %s, %s, %s" % (request.form['username'] , request.form['password'],request.form['email']))
    logging.warning("Post Request, registering user")
    user = User(request.form['username'] , request.form['password'],request.form['email'])
    logging.warning("User made")
    db.session.add(user)
    db.session.commit()
    logging.warning("User commited to DB")
    flash('User successfully registered')
    return redirect(url_for('login'))
"""
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return app.send_static_file("login.html")
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))

@app.route("/settings")
@login_required
def settings():
    return app.send_static_file("settings.html")

@app.route("/logout")
def logout():
    pop_login_session()
    return redirect(url_for('index'))
"""

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

@app.route('/user', methods=['POST'])
def user():
  u = User(request.form['name'], request.form['email'])
  db.session.add(u)
  db.session.commit()
  return redirect(url_for('index'))

@app.route('/calendars', methods=['get'])
def viewcals():
    return render_template('calendars.html', calendars=CalDB.query.all())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
