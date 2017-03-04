__author__ = "Maxwell Bo, Charleton Groves, Hugo Kawamata"

"""
This module implements the Google JSON Style Guide,
(https://google.github.io/styleguide/jsoncstyleguide.xml)
but is abstracted so as to allow changing the JSON API format without
difficulty.
"""

import typing

from flask import Response, jsonify

"""
http://www.ietf.org/rfc/rfc2616.txt
"""
class APIException(Exception):
    def __init__(self, status_code: int, message: str, payload: dict=None) -> None:
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self):
        error = {"code": self.status_code, "message": self.message}
        if self.payload:
            error["payload"] = self.payload
        return {"error": error}

"""
The server encountered an unexpected condition which prevented it
   from fulfilling the request.
"""


class InternalServerError(APIException):
    def __init__(self, message: str="Internal Server Error", payload: dict=None) -> None:
        super().__init__(status_code=500, message=message, payload=payload)


def _data(status_code, data: any) -> Response:
    response = jsonify({"data": data} if data else {})
    response.status_code = status_code
    return response


def ok(data=None) -> Response:
    return _data(200, data)


def created(data=None) -> Response:
    return _data(201, data)
