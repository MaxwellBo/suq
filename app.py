__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

# Builtins
import os
from os.path import abspath, join
from typing import *

# Libraries
from flask import Flask, jsonify, request, render_template, redirect, url_for # type: ignore
from werkzeug.utils import secure_filename
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# Imports
from suq.responses import *
from suq.models import *

### GLOBALS ###

app = Flask(__name__)
UPLOAD_FOLDER = abspath('uploads/') # TODO: Make this folder if it doesn't exist
ALLOWED_EXTENSIONS = set(['ics'])
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')

### BINDINGS ###

# Where db is imported from suq.models
# http://stackoverflow.com/questions/9692962/flask-sqlalchemy-import-context-issue


app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
db.init_app(app)
with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.commit()

# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error):
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

### UTILS ###

def allowed_file(filename: str):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

### ENDPOINTS ###

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', users=User.query.all(), calendars=CalDB.query.all())

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
