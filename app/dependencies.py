"""Reusable FastAPI dependencies."""

from typing import Annotated

from afip_services import WSN, WSNService
from fastapi import Depends, Request

from app.exceptions import ServiceException
from app.security import verify_token


def get_wsn_client(request: Request, service_enum: WSNService) -> WSN:
    """Fetch the WSN client for *service_enum* from app state, or 503 if absent."""
    clients: dict[WSNService, WSN] = getattr(request.app.state, "wsn_clients", {}) or {}
    client = clients.get(service_enum)
    if client is None:
        raise ServiceException(
            f"Service {service_enum.name} is not available",
            status_code=503,
            code="service_unavailable",
        )
    return client


CurrentUser = Annotated[dict, Depends(verify_token)]
