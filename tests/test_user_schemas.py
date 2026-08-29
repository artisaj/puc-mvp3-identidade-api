"""Testes para os contratos públicos de usuário."""

from datetime import datetime, timezone

from app.db.models.user import User
from app.schemas.user import UserRead


def test_user_read_does_not_expose_password_hash() -> None:
    """O contrato de resposta não deve expor a credencial persistida."""
    now = datetime.now(timezone.utc)
    user = User(
        id="user-id",
        name="Ana Silva",
        email="ana@example.com",
        password_hash="hashed-password",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    payload = UserRead.model_validate(user).model_dump()

    assert payload["email"] == "ana@example.com"
    assert "password_hash" not in payload
