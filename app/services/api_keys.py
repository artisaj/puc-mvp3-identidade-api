"""Regras de emissão, consulta e validação de chaves de API."""

from datetime import datetime, timezone
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_refresh_token, verify_refresh_token
from app.db.models.api_key import ApiKey
from app.db.models.user import User
from app.schemas.api_key import ApiKeyCreate


def create_api_key(db: Session, user: User, payload: ApiKeyCreate) -> tuple[ApiKey, str]:
    """Cria uma chave e retorna seu segredo somente para a resposta de criação."""
    secret = token_urlsafe(48)
    key = ApiKey(
        user_id=user.id,
        public_key_id=f"ilk_{token_urlsafe(18)}",
        secret_hash=hash_refresh_token(secret),
        name=payload.name.strip(),
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key, secret


def list_api_keys(db: Session, user_id: str) -> list[ApiKey]:
    """Lista as chaves da conta, inclusive as revogadas para fins de auditoria."""
    return list(db.scalars(select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())))


def revoke_api_key(db: Session, key: ApiKey) -> None:
    """Revoga definitivamente uma chave de API."""
    if key.is_active:
        key.is_active = False
        key.revoked_at = datetime.now(timezone.utc)
        db.commit()


def authenticate_api_key(db: Session, key_id: str, secret: str) -> ApiKey | None:
    """Valida uma chave ativa e registra seu último uso sem expor a credencial."""
    key = db.scalar(select(ApiKey).where(ApiKey.public_key_id == key_id))
    if key is None or not key.is_active or key.revoked_at is not None or not key.user.is_active:
        return None
    if not verify_refresh_token(secret, key.secret_hash):
        return None
    key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(key)
    return key