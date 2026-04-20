"""Business layer — orchestrates calls to the external `afip_services` package."""

from typing import Any

from afip_services import WSN, WSNService

from app.config import settings
from app.exceptions import AFIPUnavailableError
from app.logger import get_logger

logger = get_logger(__name__)


def initialize_services() -> tuple[WSN, WSN]:
    """Build + authenticate both WSN clients (inscription + padrón)."""
    logger.info(
        "Initializing AFIP WSN clients (is_production=%s)", settings.is_production
    )

    wsn_inscription = WSN(
        WSNService.WS_SR_CONSTANCIA_INSCRIPCION,
        settings.certificate_path,
        settings.private_key_path,
        settings.is_production,
        settings.passphrase,
    )
    wsn_inscription.obtain_authorization_ticket()

    wsn_padron = WSN(
        WSNService.WS_SR_PADRON_A13,
        settings.certificate_path,
        settings.private_key_path,
        settings.is_production,
        settings.passphrase,
    )
    wsn_padron.obtain_authorization_ticket()

    logger.info("AFIP WSN clients initialized")
    return wsn_inscription, wsn_padron


def fetch_personas(service: WSN, persona_ids: list[int]) -> list[dict[str, Any]]:
    """Delegate to the underlying WSN client to fetch persona data."""
    return service.request_persona_list(persona_ids)


def check_service_health(service: WSN, service_name: str) -> dict[str, str]:
    """Run the dummy endpoint against AFIP."""
    try:
        ok = service.request_afip_dummy()
    except Exception as exc:  # pragma: no cover
        logger.exception("AFIP dummy failed for %s", service_name)
        raise AFIPUnavailableError(str(exc)) from exc

    status_str = "UP" if ok else "DOWN"
    return {
        "service": service_name,
        "status": status_str,
        "message": f"AFIP service {service_name} is {status_str}",
    }
