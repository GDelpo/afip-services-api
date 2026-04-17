from fastapi import APIRouter, Depends

from app.api.utils import PersonaRequest, check_service_health, fetch_data_from_wsn
from app.core.dependencies import get_inscription_service
from app.core.logger import get_logger
from app.core.security import verify_token

logger = get_logger(__name__)
router = APIRouter()


@router.post("")
async def get_inscription(
    payload: PersonaRequest,
    service=Depends(get_inscription_service),
    current_user: dict = Depends(verify_token),
):
    logger.debug(
        f"Solicitud de inscripción recibida para IDs: {
            payload.persona_ids}"
    )
    data = fetch_data_from_wsn(service, payload.persona_ids)
    logger.debug(f"Datos de inscripción obtenidos para: {payload.persona_ids}")
    return {"data": data}


@router.get("/health")
async def health_inscription(
    service=Depends(get_inscription_service), current_user: dict = Depends(verify_token)
):
    logger.debug("Chequeando salud del servicio de inscripción")
    response = check_service_health(service, "WS_SR_CONSTANCIA_INSCRIPCION")
    logger.debug("Salud del servicio de inscripción verificada")
    return response
