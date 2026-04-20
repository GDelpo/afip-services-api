"""Custom middlewares: ProxyHeaders (X-Forwarded-*) + RequestLogging."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.logger import get_logger

logger = get_logger(__name__)


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Honor X-Forwarded-Proto / X-Forwarded-Prefix from Traefik or any reverse proxy.

    Sets scope["root_path"] from X-Forwarded-Prefix so FastAPI/Jinja2 generate
    correct absolute URLs when mounted behind a path-prefix router.
    """

    async def dispatch(self, request: Request, call_next):  # noqa: D401
        forwarded_prefix = request.headers.get("x-forwarded-prefix")
        if forwarded_prefix:
            request.scope["root_path"] = forwarded_prefix.rstrip("/")
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            request.scope["scheme"] = forwarded_proto.split(",")[0].strip()
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Assign a request-id and log method/path/status/latency for every request."""

    def __init__(self, app: ASGIApp, *, exclude_paths: tuple[str, ...] = ("/health",)):
        super().__init__(app)
        self.exclude_paths = exclude_paths

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: D401
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "Unhandled error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        if request.url.path not in self.exclude_paths:
            logger.info(
                "request_complete",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )
        return response
