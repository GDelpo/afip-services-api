from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logger import get_logger

logger = get_logger(__name__)


def add_exception_handlers(app):
    # Handler para excepciones HTTPException (ya se usan en tus endpoints)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTPException en {request.url}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP error", "detail": exc.detail},
        )

    # Handler para errores de validación de Pydantic
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.error(f"Error de validación en {request.url}: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "detail": exc.errors()},
        )

    # Handler para capturar cualquier otra excepción (por ejemplo, errores en
    # la comunicación con AFIP)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Error no controlado en {
                request.url}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "Ocurrió un error inesperado. Por favor, intente más tarde.",
            },
        )
