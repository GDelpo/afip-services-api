from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core import security
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("", summary="Generate JWT access token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug(f"Intento de login para el usuario: {form_data.username}")
    if (
        form_data.username != settings.auth_username
        or form_data.password != settings.auth_password
    ):
        logger.warning(
            f"Credenciales incorrectas para el usuario: {
                form_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.auth_expires_in)
    access_token = security.create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires,
    )
    logger.info(f"Usuario autenticado: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
