# Modelo para validar la entrada de datos: lista de enteros con mínimo 1 y
# máximo 250 elementos.
from typing import List

from pydantic import BaseModel, Field


class PersonaRequest(BaseModel):
    persona_ids: List[int] = Field(..., min_items=1, max_items=250)


def fetch_data_from_wsn(service, nit_list):
    """Realiza la llamada al servicio de AFIP para obtener datos asociados a los NITs."""
    return service.request_persona_list(nit_list)


def check_service_health(service, service_name: str):
    """Verifica el estado del servicio utilizando request_afip_dummy y retorna una respuesta."""
    is_active = service.request_afip_dummy()
    if is_active:
        return {
            f"{service_name.lower()}_status": "UP",
            "message": f"El servicio de {service_name} está operativo.",
        }
    else:
        return {
            f"{service_name.lower()}_status": "DOWN",
            "message": f"El servicio de {service_name} no está operativo.",
        }
