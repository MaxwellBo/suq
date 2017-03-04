__author__ = "Maxwell Bo, Charleton Groves, Hugo Kawamata"

from flask import Flask, jsonify # type: ignore
from typing import *

from suq.responses import *

### GLOBALS ###
UPLOAD_FOLDER = '/calendars'
ALLOWED_EXTENSIONS = set(['ics'])

app = Flask(__name__)

### BINDINGS

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
