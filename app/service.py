"""Business layer — builds WSN clients from the catalog and delegates calls."""

from typing import Any

from afip_services import WSN, WSNService, get_catalog

from app.config import settings
from app.exceptions import AFIPUnavailableError
from app.logger import get_logger

logger = get_logger(__name__)


# Kinds we can auto-wire to a POST /<slug> + GET /<slug>/health pair.
AUTO_KINDS = {"padron_list", "padron_single"}


def initialize_clients() -> dict[WSNService, WSN]:
    """Iterate the catalog and build one authenticated WSN client per service.

    Services with a ``kind`` outside ``AUTO_KINDS`` are skipped (they need a
    custom handler + manually-defined routes).

    Returns a dict keyed by the ``WSNService`` enum member; callers store it
    in ``app.state.wsn_clients`` so request handlers can look up their client
    by enum key.
    """
    logger.info(
        "Initializing AFIP WSN clients from catalog (is_production=%s)",
        settings.is_production,
    )
    clients: dict[WSNService, WSN] = {}

    for name, cfg in get_catalog().items():
        if cfg.kind not in AUTO_KINDS:
            logger.info(
                "Skipping service %s (kind=%s is not auto-wired; "
                "register a custom route manually)",
                name,
                cfg.kind,
            )
            continue

        service_enum = WSNService[name]
        try:
            client = WSN(
                service_enum,
                settings.certificate_path,
                settings.private_key_path,
                settings.is_production,
                settings.passphrase,
            )
            client.obtain_authorization_ticket()
            clients[service_enum] = client
            logger.info("Initialized WSN client for %s (slug=%s)", name, cfg.slug)
        except Exception:
            logger.exception("Failed to initialize WSN client for %s", name)
            # Keep starting — other services may still work; the route for
            # this one will return 503 at call time.

    logger.info("Ready — %d/%d services initialized", len(clients), len(get_catalog()))
    return clients


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
