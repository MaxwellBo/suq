__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"
import os
from os.path import abspath, join
from typing import *

from flask import Flask, jsonify, request, render_template, redirect, url_for # type: ignore
from werkzeug.utils import secure_filename

from suq.responses import *

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

from flask_sqlalchemy import SQLAlchemy

### GLOBALS ###
UPLOAD_FOLDER = abspath('calendars')
ALLOWED_EXTENSIONS = set(['ics'])
# Base is the base table declarer that all table classes take
Base = declarative_base()

app = Flask(__name__)


DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

### BINDINGS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  
    email = db.Column(db.String(100))
    def __init__(self, name, email):
        self.name = name
        self.email = email
    def __repr__(self):
        return '<Name %r>' % self.name
# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(APIException)
def handle_thrown_api_exceptions(error):
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

### TESTING ###

@app.route("/ok")
def result():
    return ok(["Here's", "your", "stuff"])

@app.route("/created")
def created_endpoint():
   return created(["I", "made", "this"])

@app.route("/error")
def error():
    raise InternalServerError(message="I made something break")

### ENDPOINTS

# http://flask.pocoo.org/docs/0.12/patterns/fileuploads/


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template('index.html', users=User.query.all())

def upload_file():
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
            filename = secure_filename(file.filename)
            path = join(app.config['UPLOAD_FOLDER'], filename)
            # http://werkzeug.pocoo.org/docs/0.11/datastructures/#werkzeug.datastructures.FileStorage.save
            file.save(path)
            return created("Calendar successfully created")

@app.route('/user', methods=['POST'])
def user():
  u = User(request.form['name'], request.form['email'])
  db.session.add(u)
  db.session.commit()
  return redirect(url_for('index'))

if __name__ == '__main__':
  db.create_all()
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
