"""Contratos de resposta para sessões."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TokenRead(BaseModel):
    """Resposta pública após emitir ou renovar um access token."""

    access_token: str
    token_type: str = "bearer"


class SessionRead(BaseModel):
    """Dados públicos de uma sessão, sem o refresh token nem seu hash."""

    id: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    last_used_at: datetime
    user_agent: str | None

    model_config = ConfigDict(from_attributes=True)
