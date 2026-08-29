"""Regras de negócio para o ciclo de vida das sessões."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_refresh_token, hash_refresh_token, verify_refresh_token
from app.db.models.session import UserSession


def utc_now() -> datetime:
    """Retorna a data e hora atual com fuso UTC."""
    return datetime.now(timezone.utc)


def is_expired(expires_at: datetime) -> bool:
    """Determina se uma expiração do banco, com ou sem fuso, já ocorreu."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= utc_now()


def create_session(db: Session, user_id: str, user_agent: str | None) -> tuple[UserSession, str]:
    """Cria uma sessão e retorna o refresh token somente para envio no cookie."""
    refresh_token = generate_refresh_token()
    expires_at = utc_now() + timedelta(days=get_settings().refresh_token_expire_days)
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, refresh_token


def get_valid_session_by_refresh_token(db: Session, refresh_token: str) -> UserSession | None:
    """Obtém a sessão ativa associada ao refresh token opaco fornecido."""
    session = db.scalar(
        select(UserSession).where(UserSession.refresh_token_hash == hash_refresh_token(refresh_token))
    )
    if session is None or session.revoked_at is not None or is_expired(session.expires_at):
        return None
    return session if verify_refresh_token(refresh_token, session.refresh_token_hash) else None


def rotate_refresh_token(db: Session, session: UserSession) -> str:
    """Substitui o refresh token persistido e registra o uso da sessão."""
    refresh_token = generate_refresh_token()
    session.refresh_token_hash = hash_refresh_token(refresh_token)
    session.last_used_at = utc_now()
    db.commit()
    return refresh_token


def revoke_session(db: Session, session: UserSession) -> None:
    """Revoga uma sessão de modo idempotente."""
    if session.revoked_at is None:
        session.revoked_at = utc_now()
        db.commit()


def list_active_sessions(db: Session, user_id: str) -> list[UserSession]:
    """Lista as sessões não revogadas e ainda válidas de um usuário."""
    sessions = list(
        db.scalars(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .order_by(UserSession.created_at.desc())
        )
    )
    return [session for session in sessions if not is_expired(session.expires_at)]