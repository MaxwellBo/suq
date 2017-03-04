class APIException(Exception):
    def __init__(self, status_code, message, payload=None):
        self.status_code = status_code
        self.message = message
        self.payload = payload

    def to_dict(self):
        rv = {"message": self.message }
        if self.payload:
            rv["payload"] = self.payload
        return rv

class InternalServerError(APIException):
    def __init__(self, message="Internal Server Error", payload=None):
        super().__init__(status_code=500, message=message, payload=payload)