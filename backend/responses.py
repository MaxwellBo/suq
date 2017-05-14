__author__ = "Maxwell Bo, Charlton Groves, Hugo Kawamata"

"""
This module implements the Google JSON Style Guide,
(https://google.github.io/styleguide/jsoncstyleguide.xml)
but is abstracted so as to allow changing the JSON API format without
difficulty.
"""

# Builtins
from typing import Any, Callable
from functools import wraps

# Libraries
from flask import Response, jsonify

"""
Helper abstract exception to create error responses adhearing to the Google JSON
style-guide.

http://www.ietf.org/rfc/rfc2616.txt
"""
class APIException(Exception):
    def __init__(self, status_code: int, message: str, payload: dict=None) -> None:
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self) -> dict:
        error = {"code": self.status_code, "message": self.message}
        if bool(self.payload):
            error["payload"] = self.payload
        return {"error": error}

"""
The request could not be understood by the server due to malformed
syntax. The client SHOULD NOT repeat the request without
modifications.
"""
class BadRequest(APIException):
    def __init__(self, message: str="Bad Request", payload: dict=None) -> None:
        super().__init__(status_code=400, message=message, payload=payload)


"""
The server understood the request, but is refusing to fulfill it.
Authorization will not help and the request SHOULD NOT be repeated.
"""
class Forbidden(APIException):
    def __init__(self, message: str="Forbidden", payload: dict=None) -> None:
        super().__init__(status_code=403, message=message, payload=payload)


"""
The server encountered an unexpected condition which prevented it
from fulfilling the request.
"""
class InternalServerError(APIException):
    def __init__(self, message: str="Internal Server Error", payload: dict=None) -> None:
        super().__init__(status_code=500, message=message, payload=payload)


"""
The server does not support the functionality required to fulfill the
request.
"""
class NotImplemented(APIException):
    def __init__(self, message: str="Not Implemented", payload: dict=None) -> None:
        super().__init__(status_code=501, message=message, payload=payload)

"""
Helper method to create non-error responses adhearing to the Google JSON
style-guide.
"""
def _result(status_code: int, data: Any) -> Response:
    response = jsonify({"result": data} if data else {})
    response.status_code = status_code
    return response


"""
The request has succeeded.
"""
def ok(data: Any = None) -> Response:
    return _result(200, data)


"""
The request has been fulfilled and resulted in a new resource being created.
"""
def created(data: Any = None) -> Response:
    return _result(201, data)

"""
Runs Flask's `jsonify` function against the return value of the annotated
function
"""
def to_json(func: Callable[..., Response]) -> Response:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Response:
        get_fun = func(*args, **kwargs)
        return jsonify(get_fun)

    return wrapper
