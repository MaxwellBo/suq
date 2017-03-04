__author__ = "Maxwell Bo, Charleton Groves, Hugo Kawamata"

"""
This module implements the Google JSON Style Guide,
(https://google.github.io/styleguide/jsoncstyleguide.xml)
but is abstracted so as to allow changing the JSON API format without
difficulty.
"""

from flask import Flask, jsonify # type: ignore
from typing import *

from suq.responses import *

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

# v http://flask.pocoo.org/docs/0.12/patterns/apierrors/
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    # ^ http://flask.pocoo.org/docs/0.12/api/#flask.json.jsonify
    response.status_code = error.status_code
    return response

"""
An endpoint to test how our errors are going to be thrown
"""
@app.route("/error")
def error():
    raise InternalServerError(message="I made something break")
