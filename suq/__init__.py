_author__ = "Maxwell Bo, Charleton Groves, Hugo Kawamata"

from flask import Flask, jsonify # type: ignore
from typing import *

from suq.responses import *

app = Flask(__name__)

@app.route("/")
def result():
    return result(200, None)

# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(Error)
def handle_thrown_errors(error):
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

@app.route("/error")
def error():
    raise InternalServerError(message="I made something break")
