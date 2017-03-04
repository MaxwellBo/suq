__author__ = "Maxwell Bo, Charleton Groves, Hugo Kawamata"

from os.path import abspath, join
from typing import *

from flask import Flask, jsonify, request # type: ignore
from werkzeug.utils import secure_filename


from suq.responses import *

### GLOBALS ###
UPLOAD_FOLDER = abspath('calendars')
ALLOWED_EXTENSIONS = set(['ics'])

app = Flask(__name__)

### BINDINGS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
def upload_file():
    if request.method == 'GET':
        return ok("here's your calendar")

    else:
        # check if the post request has a file part
        if 'file' not in request.files:
            return ok("No file part") # TODO: Change this to an exception

        file = request.files['file']

        # check if an empty file was sent
        if file.filename == '':
            return ok("No file was selected") # TODO: Change this to an exception

        if not allowed_file(file.filename):
            return ok("Filetype not permitted") # TODO: Change to exceptions

        if file:
            filename = secure_filename(file.filename)
            path = join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            return created("Calendar successfully created")


