"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "AFIP Services API"
    app_version: str = "0.2.0"
    app_description: str = (
        "REST API FastAPI that wraps AFIP/ARCA SOAP web services (WSAA + WSN)."
    )
    app_author: str = "Guido Delponte"
    app_author_email: str = "guido_delponte@hotmail.com"

    environment: Literal["dev", "staging", "prod"] = "prod"
    debug: bool = False

    # Logging
    log_dir_path: str = "logs"
    log_format: Literal["json", "text"] = "json"
    logtail_token: str | None = None

    # Auth (local single-user fallback + JWT)
    auth_username: str
    auth_password: str
    auth_secret_key: str
    auth_algorithm: str = "HS256"
    auth_expires_in: int = 30  # minutes

    # API
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # AFIP WSN
    certificate_path: str
    private_key_path: str
    passphrase: str | None = None

    # SlowAPI
    rate_limit_time: int = 60
    max_calls: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def _resolve_log_format(self) -> "Settings":
        # Keep JSON in prod; dev/debug users can set LOG_FORMAT=text.
        return self

    @computed_field
    @property
    def is_production(self) -> bool:
        """Used by the AFIP client to pick WSDL endpoints."""
        return self.environment == "prod" and not self.debug

    @computed_field
    @property
    def rate_limit_str(self) -> str:
        return f"{self.max_calls}/{self.rate_limit_time} seconds"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
