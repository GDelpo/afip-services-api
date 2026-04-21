"""FastAPI router — exposes /token + one auto-registered POST/GET pair per catalog entry."""

from datetime import timedelta

from afip_services import WSNService, get_catalog
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.dependencies import CurrentUser, get_wsn_client
from app.logger import get_logger
from app.schemas import (
    AFIPServiceStatus,
    PersonaRequest,
    PersonaResponse,
    TokenResponse,
)
from app.security import create_access_token
from app.service import AUTO_KINDS, check_service_health, fetch_personas

logger = get_logger(__name__)

router = APIRouter()


# ── Auth ──────────────────────────────────────────────────────────────────────


@router.post("/token", response_model=TokenResponse, tags=["AUTH"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """Exchange username/password for a JWT access token."""
    if (
        form_data.username != settings.auth_username
        or form_data.password != settings.auth_password
    ):
        logger.warning("Failed login attempt for user %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=settings.auth_expires_in),
    )
    logger.info("User authenticated: %s", form_data.username)
    return TokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.auth_expires_in,
    )


# ── Auto-registered routes from the catalog ───────────────────────────────────
#
# Every service in afip-services' catalog with a built-in kind gets a pair:
#   POST /<slug>         — query by list of CUITs
#   GET  /<slug>/health  — reach the AFIP service's dummy endpoint
#
# Custom-kind services (wsfe, etc.) are skipped here; add their routes manually.


def _build_query_endpoint(service_enum: WSNService):
    async def endpoint(
        payload: PersonaRequest,
        request: Request,
        _: CurrentUser,
    ) -> PersonaResponse:
        service = get_wsn_client(request, service_enum)
        logger.debug("%s request for %d ids", service_enum.name, len(payload.persona_ids))
        data = fetch_personas(service, payload.persona_ids)
        return PersonaResponse(data=data)

    endpoint.__name__ = f"query_{service_enum.name.lower()}"
    return endpoint


def _build_health_endpoint(service_enum: WSNService):
    async def endpoint(
        request: Request,
        _: CurrentUser,
    ) -> AFIPServiceStatus:
        service = get_wsn_client(request, service_enum)
        return AFIPServiceStatus(**check_service_health(service, service_enum.name))

    endpoint.__name__ = f"health_{service_enum.name.lower()}"
    return endpoint


def _register_catalog_routes(router: APIRouter) -> None:
    """Iterate the AFIP catalog and register POST/GET per service."""
    for name, cfg in get_catalog().items():
        if cfg.kind not in AUTO_KINDS:
            continue
        service_enum = WSNService[name]
        tag = cfg.slug.upper()
        summary = cfg.description or f"Query {name}"

        router.add_api_route(
            f"/{cfg.slug}",
            _build_query_endpoint(service_enum),
            methods=["POST"],
            response_model=PersonaResponse,
            tags=[tag],
            summary=summary,
        )
        router.add_api_route(
            f"/{cfg.slug}/health",
            _build_health_endpoint(service_enum),
            methods=["GET"],
            response_model=AFIPServiceStatus,
            tags=[tag],
            summary=f"Dummy ping for {name}",
        )


_register_catalog_routes(router)
