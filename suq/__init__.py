from flask import Flask # type: ignore
from typing import *

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"
