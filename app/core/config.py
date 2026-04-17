from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # App settings
    debug: bool
    app_name: str = "AFIP | ARCA - WSN TO API"
    app_version: str = "0.1.0"
    app_description: str = "La integración de AFIP | ARCA - WSN con FastAPI"
    app_author: str = "Guido Delponte"
    app_author_email: str = "delponte.guidon@gmail.com"

    # logging settings
    log_dir_path: str
    logtail_token: str | None = None

    # Auth settings
    auth_username: str
    auth_password: str
    auth_secret_key: str
    auth_algorithm: str = "HS256"
    auth_expires_in: int = 30

    # API settings
    api_prefix: str = "/api"
    api_version: str = "v1"

    # AFIP WSN settings
    certificate_path: str
    private_key_path: str
    passphrase: str | None = None

    # SlowAPI settings
    rate_limit_time: int = 60
    max_calls: int = 1

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
