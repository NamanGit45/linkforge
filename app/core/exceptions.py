class AppException(Exception):
    """Base class for every error we raise on purpose."""

    status_code: int = 500
    code: str = "internal_error"  # stable, machine-readable
    message: str = "Something went wrong"  # default human-readable text
    headers: dict[str, str] | None = None

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"
    message = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"
    message = "Resource already exists"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"
    message = "Authentication required"
    # The HTTP spec says 401 responses should say which scheme to use
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(AppException):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to do this"


class InternalError(AppException):
    status_code = 500
    code = "internal_error"


class BadRequestError(AppException):
    status_code = 400
    code = "bad_request"
    message = "Bad request"
