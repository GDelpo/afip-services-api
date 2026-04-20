"""Service-level exceptions + FastAPI exception handlers."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.logger import get_logger

logger = get_logger(__name__)


class ServiceException(Exception):
    """Domain exception raised by the business layer.

    Handlers below translate it to JSON responses with a stable shape.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "service_error",
        detail: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.detail = detail or {}


class AFIPUnavailableError(ServiceException):
    def __init__(self, message: str = "AFIP service is not operational"):
        super().__init__(message, status_code=503, code="afip_unavailable")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceException)
    async def _service_exception_handler(request: Request, exc: ServiceException):
        logger.warning(
            "ServiceException: %s",
            exc.message,
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
                "code": exc.code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        logger.info(
            "HTTPException on %s: %s",
            request.url.path,
            exc.detail,
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "message": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.info(
            "Validation error on %s",
            request.url.path,
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
