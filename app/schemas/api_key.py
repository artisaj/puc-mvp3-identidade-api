"""Contratos públicos para chaves de API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import TokenRead


class ApiKeyCreate(BaseModel):
    """Dados para nomear uma nova chave de API."""

    name: str = Field(min_length=1, max_length=120)


class ApiKeyRead(BaseModel):
    """Metadados seguros de uma chave, sem seu segredo ou hash."""

    id: str
    public_key_id: str
    name: str
    is_active: bool
    revoked_at: datetime | None
    created_at: datetime
    last_used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreated(ApiKeyRead):
    """Resposta exclusiva de criação, que revela o segredo uma única vez."""

    secret: str


class ApiKeyLogin(BaseModel):
    """Par de credenciais usado para trocar uma chave por JWT de acesso."""

    key_id: str = Field(min_length=1, max_length=80)
    secret: str = Field(min_length=1, max_length=255)


ApiKeyTokenRead = TokenRead