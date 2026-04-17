from fastapi import APIRouter

from app.api import auth, inscription, padron
from app.core.config import settings  # Asegúrate de que la ruta sea correcta

api_router = APIRouter()

app_prefix = f"{settings.api_prefix}/{settings.api_version}"

routers = [
    (inscription.router, "/inscription", ["inscription"]),
    (padron.router, "/padron", ["padron"]),
    (auth.router, "/token", ["auth"]),
]

for router, endpoint_prefix, endpoint_tags in routers:
    api_router.include_router(
        router,
        prefix=f"{app_prefix}{endpoint_prefix}",
        tags=[tag.upper() for tag in endpoint_tags],
    )
