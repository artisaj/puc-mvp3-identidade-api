"""Regras de domínio para a redefinição de senha sem e-mail."""

from hmac import compare_digest

import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    password_hash_fingerprint,
)
from app.db.models.user import User
from app.services.sessions import revoke_all_sessions
from app.services.users import get_user_by_id


def issue_development_reset_token(user: User | None) -> str | None:
    """Emite token apenas para uma conta ativa quando a API roda em desenvolvimento."""
    if get_settings().app_env.lower() != "development" or user is None or not user.is_active:
        return None
    return create_password_reset_token(user.id, user.password_hash)


def reset_password(db: Session, token: str, new_password: str) -> None:
    """Troca a senha, invalida o token usado e revoga todas as sessões existentes."""
    try:
        user_id, token_fingerprint = decode_password_reset_token(token)
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid or expired password reset token") from exc

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active or not compare_digest(
        token_fingerprint, password_hash_fingerprint(user.password_hash)
    ):
        raise ValueError("Invalid or expired password reset token")

    user.password_hash = hash_password(new_password)
    revoke_all_sessions(db, user.id)
    db.commit()