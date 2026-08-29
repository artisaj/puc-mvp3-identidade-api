"""Testes unitários das primitivas de segurança."""

from datetime import timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)


@pytest.fixture
def configured_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configura uma chave efêmera apenas para os testes de JWT."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-jwt-secret-with-at-least-32-bytes")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_password_hash_uses_argon2_and_verifies_credentials() -> None:
    """A senha deve ser verificável, sem permanecer em texto puro."""
    password = "Senha-forte-123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("senha-incorreta", password_hash)


def test_access_token_round_trip(configured_jwt_secret: None) -> None:
    """Um token criado pela aplicação deve recuperar o mesmo sujeito."""
    token = create_access_token("user-id")

    assert decode_access_token(token) == "user-id"


def test_expired_access_token_is_rejected(configured_jwt_secret: None) -> None:
    """Tokens já expirados não devem ser aceitos."""
    token = create_access_token("user-id", expires_delta=timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_refresh_token_is_opaque_and_verified_by_hash() -> None:
    """A API deve persistir somente a representação hash do token opaco."""
    token = generate_refresh_token()
    token_hash = hash_refresh_token(token)

    assert token_hash != token
    assert verify_refresh_token(token, token_hash)
    assert not verify_refresh_token("other-token", token_hash)
