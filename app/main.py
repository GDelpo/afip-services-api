"""App factory + lifespan. Entry point for gunicorn: `app.main:app`."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import router as api_router
from app.config import settings
from app.dashboard.routes import router as dashboard_router
from app.exceptions import register_exception_handlers
from app.limiter import limiter
from app.logger import configure_logging, get_logger
from app.middleware import ProxyHeadersMiddleware, RequestLoggingMiddleware
from app.schemas import HealthResponse
from app.service import initialize_services

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401
    """Initialize AFIP WSN clients at startup and release them at shutdown."""
    logger.info("Starting %s v%s (environment=%s)",
                settings.app_name, settings.app_version, settings.environment)
    try:
        wsn_inscription, wsn_padron = initialize_services()
    except Exception:
        logger.exception("Could not initialize AFIP services")
        # Still allow the app to come up so /health and /dashboard/login work
        wsn_inscription = None
        wsn_padron = None

    app.state.wsn_inscription_service = wsn_inscription
    app.state.wsn_padron_service = wsn_padron
    logger.info("AFIP services ready")
    try:
        yield
    finally:
        app.state.wsn_inscription_service = None
        app.state.wsn_padron_service = None
        logger.info("AFIP services released")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        contact={
            "name": settings.app_author,
            "email": settings.app_author_email,
        },
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Middleware order: ProxyHeaders → RequestLogging → CORS → SlowAPI
    app.add_middleware(ProxyHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)

    # Rate limiter state + handler
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request, exc):  # noqa: ARG001
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": f"Too many requests: {exc.detail}",
            },
        )

    # Exception handlers (ServiceException, HTTPException, validation, generic)
    register_exception_handlers(app)

    # Routers
    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(dashboard_router, prefix="/dashboard")

    # Health — always at root, NOT under /api/v1
    @app.get("/health", response_model=HealthResponse, tags=["STATUS"])
    async def health() -> HealthResponse:
        return HealthResponse(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )

    return app


app = create_app()
