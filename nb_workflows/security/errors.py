from sanic.exceptions import SanicException
from sanic.exceptions import Unauthorized as SanicUnauthorized


class SanicJWTException(SanicException):
    pass


class InvalidToken(SanicJWTException):
    pass


class WebAuthFailed(SanicJWTException):
    status_code = 401
    quiet = True

    def __init__(self, message="Authentication failed.", **kwargs):
        super().__init__(message, **kwargs)


class MissingAuthorizationHeader(SanicJWTException):
    status_code = 400

    def __init__(self, message="Authorization header not present.", **kwargs):
        super().__init__(message, **kwargs)


class Unauthorized(SanicJWTException, SanicUnauthorized):
    def __init__(self, message="Auth required.", **kwargs):
        super().__init__(message, scheme="Bearer", **kwargs)


class AuthValidationFailed(Exception):
    pass
