"""
http://www.ietf.org/rfc/rfc2616.txt
"""
class APIException(Exception):
    def __init__(self, status_code, message, payload=None):
        self.status_code = status_code
        self.message = message
        self.payload = payload

    # https://google.github.io/styleguide/jsoncstyleguide.xml#General_Guidelines
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
    def __init__(self, message="Internal Server Error", payload=None):
        super().__init__(status_code=500, message=message, payload=payload)
