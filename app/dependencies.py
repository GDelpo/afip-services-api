"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.exceptions import ServiceException
from app.security import verify_token


def get_inscription_service(request: Request):
    """Return the AFIP inscription WSN client kept in app.state."""
    service = getattr(request.app.state, "wsn_inscription_service", None)
    if service is None:
        raise ServiceException(
            "Inscription service is not available",
            status_code=503,
            code="service_unavailable",
        )
    return service


def get_padron_service(request: Request):
    """Return the AFIP padrón WSN client kept in app.state."""
    service = getattr(request.app.state, "wsn_padron_service", None)
    if service is None:
        raise ServiceException(
            "Padrón service is not available",
            status_code=503,
            code="service_unavailable",
        )
    return service


CurrentUser = Annotated[dict, Depends(verify_token)]
InscriptionService = Annotated[object, Depends(get_inscription_service)]
PadronService = Annotated[object, Depends(get_padron_service)]
