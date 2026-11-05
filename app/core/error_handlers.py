import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger("linkforge.errors")

# For errors FastAPI/Starlette raise themselves (unknown route, wrong method, ...)
HTTP_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "too_many_requests",
}


def error_response(
    status_code, code, message, details=None, headers=None
) -> JSONResponse:
    """The ONE place that defines what an error looks like."""
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:

    # 1. Our own errors (NotFoundError, ConflictError, ...)
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        if exc.status_code >= 500:
            logger.error("%s %s -> %s", request.method, request.url.path, exc.message)
        return error_response(
            exc.status_code, exc.code, exc.message, headers=exc.headers
        )

    # 2. Errors raised by the framework (also catches FastAPI's HTTPException,
    #    e.g. the 401 from oauth2_scheme when the header is missing)
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        code = HTTP_STATUS_CODES.get(exc.status_code, "http_error")
        return error_response(
            exc.status_code, code, str(exc.detail), headers=exc.headers
        )

    # 3. Pydantic validation failures (422)
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # We build details ourselves instead of dumping exc.errors(): errors from
        # custom validators can contain Python exception objects that aren't JSON-safe.
        details = [
            {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return error_response(
            422, "validation_error", "Request validation failed", details=details
        )

    # 4. Safety net: anything we didn't anticipate
    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Full traceback goes to OUR logs; the client gets a generic message only.
        # Never send str(exc) to the client: it can leak table names, file paths, SQL.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return error_response(500, "internal_error", "Internal server error")
