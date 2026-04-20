"""Pydantic request/response schemas — camelCase JSON via alias_generator."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class HealthResponse(_CamelModel):
    name: str
    version: str
    status: str = "ok"
    environment: str


class TokenResponse(_CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class PersonaRequest(_CamelModel):
    persona_ids: list[int] = Field(..., min_length=1, max_length=250)


class PersonaResponse(_CamelModel):
    data: list[dict[str, Any]]


class AFIPServiceStatus(_CamelModel):
    service: str
    status: str
    message: str
