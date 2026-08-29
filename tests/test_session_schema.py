"""Testes para contratos de sessão."""

from datetime import datetime, timedelta, timezone

from app.db.models.session import UserSession
from app.schemas.session import SessionRead


def test_session_read_does_not_expose_refresh_token_hash() -> None:
    """A resposta não deve revelar o token de renovação persistido."""
    now = datetime.now(timezone.utc)
    session = UserSession(
        id="session-id",
        user_id="user-id",
        refresh_token_hash="hashed-refresh-token",
        expires_at=now + timedelta(days=7),
        created_at=now,
        last_used_at=now,
    )

    payload = SessionRead.model_validate(session).model_dump()

    assert payload["id"] == "session-id"
    assert "refresh_token_hash" not in payload
