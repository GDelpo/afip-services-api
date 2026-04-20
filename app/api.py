"""FastAPI router — exposes /token, /inscription, /padron under the versioned prefix."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.dependencies import (
    CurrentUser,
    InscriptionService,
    PadronService,
)
from app.logger import get_logger
from app.schemas import (
    AFIPServiceStatus,
    PersonaRequest,
    PersonaResponse,
    TokenResponse,
)
from app.security import create_access_token
from app.service import check_service_health, fetch_personas

logger = get_logger(__name__)

router = APIRouter()


# ── Auth ──────────────────────────────────────────────────────────────────────


@router.post("/token", response_model=TokenResponse, tags=["AUTH"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
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


# ── Inscription ───────────────────────────────────────────────────────────────


@router.post(
    "/inscription",
    response_model=PersonaResponse,
    tags=["INSCRIPTION"],
)
async def get_inscription(
    payload: PersonaRequest,
    service: InscriptionService,
    _: CurrentUser,
) -> PersonaResponse:
    """Query the AFIP constancia-de-inscripción WSN for a list of CUITs."""
    logger.debug("Inscription request for %d ids", len(payload.persona_ids))
    data = fetch_personas(service, payload.persona_ids)
    return PersonaResponse(data=data)


@router.get(
    "/inscription/health",
    response_model=AFIPServiceStatus,
    tags=["INSCRIPTION"],
)
async def health_inscription(
    service: InscriptionService,
    _: CurrentUser,
) -> AFIPServiceStatus:
    """Ping AFIP inscription service via dummy method."""
    return AFIPServiceStatus(**check_service_health(service, "WS_SR_CONSTANCIA_INSCRIPCION"))


# ── Padrón ────────────────────────────────────────────────────────────────────


@router.post(
    "/padron",
    response_model=PersonaResponse,
    tags=["PADRON"],
)
async def get_padron(
    payload: PersonaRequest,
    service: PadronService,
    _: CurrentUser,
) -> PersonaResponse:
    """Query the AFIP padrón A13 WSN for a list of CUITs."""
    logger.debug("Padrón request for %d ids", len(payload.persona_ids))
    data = fetch_personas(service, payload.persona_ids)
    return PersonaResponse(data=data)


@router.get(
    "/padron/health",
    response_model=AFIPServiceStatus,
    tags=["PADRON"],
)
async def health_padron(
    service: PadronService,
    _: CurrentUser,
) -> AFIPServiceStatus:
    """Ping AFIP padrón service via dummy method."""
    return AFIPServiceStatus(**check_service_health(service, "WS_SR_PADRON_A13"))
