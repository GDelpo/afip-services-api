"""JWT security helpers — create + verify access tokens."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/token")


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Generate a signed JWT with the given payload."""
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.auth_expires_in)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.auth_secret_key, algorithm=settings.auth_algorithm
    )


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode & validate a JWT. Returns the payload dict."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
    except JWTError as exc:
        raise credentials_exc from exc
    if payload.get("sub") is None:
        raise credentials_exc
    return payload
