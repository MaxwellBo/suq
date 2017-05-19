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

class APIException(Exception):
    """
    Helper abstract exception to create error responses adhearing to the Google JSON
    style-guide.

    http://www.ietf.org/rfc/rfc2616.txt
    """

    def __init__(self, status_code: int, message: str, payload: dict=None) -> None:
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self) -> dict:
        error = {"code": self.status_code, "message": self.message}
        if bool(self.payload):
            error["payload"] = self.payload
        return {"error": error}

class BadRequest(APIException):
    """
    The request could not be understood by the server due to malformed
    syntax. The client SHOULD NOT repeat the request without
    modifications.
    """

    def __init__(self, message: str="Bad Request", payload: dict=None) -> None:
        super().__init__(status_code=400, message=message, payload=payload)

class Forbidden(APIException):
    """
    The server understood the request, but is refusing to fulfill it.
    Authorization will not help and the request SHOULD NOT be repeated.
    """

    def __init__(self, message: str="Forbidden", payload: dict=None) -> None:
        super().__init__(status_code=403, message=message, payload=payload)


class NotFound(APIException):
    """
    The server has not found anything matching the Request-URI. No
    indication is given of whether the condition is temporary or permanent.
    """
    
    def __init__(self, message: str="Not Implemented", payload: dict=None) -> None:
        super().__init__(status_code=404, message=message, payload=payload)


class InternalServerError(APIException):
    """
    The server encountered an unexpected condition which prevented it
    from fulfilling the request.
    """

    def __init__(self, message: str="Internal Server Error", payload: dict=None) -> None:
        super().__init__(status_code=500, message=message, payload=payload)


class NotImplemented(APIException):
    """
    The server does not support the functionality required to fulfill the
    request.
    """

    def __init__(self, message: str="Not Implemented", payload: dict=None) -> None:
        super().__init__(status_code=501, message=message, payload=payload)


def _data(status_code: int, data: Any) -> Response:
    """
    Helper method to create non-error responses adhearing to the Google JSON
    style-guide.
    """
    response = jsonify({"data": data} if data else {})
    response.status_code = status_code
    return response


def ok(data: Any = None) -> Response:
    """
    The request has succeeded.
    """
    return _data(200, data)


def created(data: Any = None) -> Response:
    """
    The request has been fulfilled and resulted in a new resource being created.
    """
    return _data(201, data)


def no_content() -> Response:
    """
    The server has fulfilled the request but does not need to return an
    entity-body, and might want to return updated metainformation.
    """
    return _data(204, None)


def to_json(func: Callable[..., Response]) -> Response:
    """
    Runs Flask's `jsonify` function against the return value of the annotated
    function
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Response:
        get_fun = func(*args, **kwargs)
        return jsonify(get_fun)

    return wrapper
