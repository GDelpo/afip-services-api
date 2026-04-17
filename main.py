from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.core.exception_handlers import add_exception_handlers
from app.core.limiter import limiter
from app.core.logger import get_logger
from app.core.service import initialize_services

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializando servicios AFIP...")
    wsn_inscription_service, wsn_padron_service = initialize_services()
    app.state.wsn_inscription_service = wsn_inscription_service
    app.state.wsn_padron_service = wsn_padron_service
    logger.info("Servicios AFIP inicializados correctamente")
    yield
    logger.info("Cerrando servicios AFIP...")
    app.state.wsn_inscription_service = None
    app.state.wsn_padron_service = None
    logger.info("Servicios AFIP cerrados")


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    author=settings.app_author,
    author_email=settings.app_author_email,
    openapi_url=f"{settings.api_prefix}/{settings.api_version}/openapi.json",
    debug=settings.debug,
)

app.state.limiter = limiter
app.include_router(api_router)

add_exception_handlers(app)


@app.get("/", tags=["STATUS"])
async def health_check():
    logger.debug("Ejecutando health_check")
    return {"name": app.title, "version": app.version, "description": app.description}


if __name__ == "__main__":
    uvicorn.run(app)
