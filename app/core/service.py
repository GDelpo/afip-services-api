from app.core.config import settings

from ..afip_ws.afip_config import WSNService
from ..afip_ws.afip_gateway import WSN

# TODO REVISAR ESTO, NO FUNCIONA EN MODO DEBUG AFIP WS
is_production = not bool(settings.debug)


def initialize_services():
    wsn_inscription_service = WSN(
        WSNService.WS_SR_CONSTANCIA_INSCRIPCION,
        settings.certificate_path,
        settings.private_key_path,
        is_production,
        settings.passphrase,
    )
    wsn_inscription_service.obtain_authorization_ticket()

    wsn_padron_service = WSN(
        WSNService.WS_SR_PADRON_A13,
        settings.certificate_path,
        settings.private_key_path,
        is_production,
        settings.passphrase,
    )
    wsn_padron_service.obtain_authorization_ticket()

    return wsn_inscription_service, wsn_padron_service
