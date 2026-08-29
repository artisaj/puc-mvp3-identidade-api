"""Testes focados dos fluxos de autenticação, perfil e sessões."""

from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    """Fornece uma API isolada com SQLite temporário e segredo de JWT efêmero."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-jwt-secret-with-at-least-32-bytes")
    get_settings.cache_clear()
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)

    def override_get_db() -> Generator[Session]:
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


def register(client: TestClient, email: str = "ana@example.com") -> None:
    response = client.post(
        "/auth/register",
        json={"name": "Ana Silva", "email": email, "password": "Senha-forte-123"},
    )
    assert response.status_code == 201


def login(client: TestClient, email: str = "ana@example.com") -> str:
    response = client.post("/auth/login", json={"email": email, "password": "Senha-forte-123"})
    assert response.status_code == 200
    assert "refresh_token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_creates_session_and_rejects_invalid_credentials(client: TestClient) -> None:
    register(client)
    invalid = client.post("/auth/login", json={"email": "ana@example.com", "password": "wrong"})
    assert invalid.status_code == 401

    token = login(client)
    sessions = client.get("/sessions", headers=bearer(token))
    assert sessions.status_code == 200
    assert len(sessions.json()) == 1


def test_refresh_rotates_token_and_logout_revokes_session(client: TestClient) -> None:
    register(client)
    login(client)
    original_token = client.cookies.get("refresh_token")

    refreshed = client.post("/auth/refresh")
    assert refreshed.status_code == 200
    assert client.cookies.get("refresh_token") != original_token

    reused = client.post("/auth/refresh", cookies={"refresh_token": original_token})
    assert reused.status_code == 401
    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    assert client.post("/auth/refresh").status_code == 401


def test_current_user_profile_requires_authentication_and_can_be_updated(client: TestClient) -> None:
    assert client.get("/users/me").status_code == 401
    register(client)
    token = login(client)

    profile = client.get("/users/me", headers=bearer(token))
    assert profile.status_code == 200
    assert profile.json()["email"] == "ana@example.com"

    updated = client.put("/users/me", headers=bearer(token), json={"name": "Ana Costa", "city": "São Paulo"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Ana Costa"
    assert updated.json()["city"] == "São Paulo"


def test_protected_routes_reject_missing_invalid_and_expired_access_tokens(client: TestClient) -> None:
    """Perfil e sessões recusam credenciais ausentes, inválidas ou expiradas."""
    for route in ("/users/me", "/sessions"):
        assert client.get(route).status_code == 401
        invalid = client.get(route, headers=bearer("not-a-jwt"))
        assert invalid.status_code == 401
        assert invalid.headers["www-authenticate"] == "Bearer"

    register(client)
    expired_token = create_access_token("unknown-user", expires_delta=timedelta(seconds=-1))
    for route in ("/users/me", "/sessions"):
        assert client.get(route, headers=bearer(expired_token)).status_code == 401


def test_revoked_session_cannot_refresh_and_is_hidden_from_active_sessions(client: TestClient) -> None:
    """A revogação pelo endpoint de sessões invalida o refresh token associado."""
    register(client)
    access_token = login(client)
    session_id = client.get("/sessions", headers=bearer(access_token)).json()[0]["id"]

    revoked = client.delete(f"/sessions/{session_id}", headers=bearer(access_token))
    assert revoked.status_code == 204
    assert client.get("/sessions", headers=bearer(access_token)).json() == []
    assert client.post("/auth/refresh").status_code == 401


def test_user_cannot_revoke_another_users_session(client: TestClient) -> None:
    register(client, "ana@example.com")
    ana_token = login(client, "ana@example.com")
    ana_session_id = client.get("/sessions", headers=bearer(ana_token)).json()[0]["id"]

    register(client, "bia@example.com")
    bia_token = login(client, "bia@example.com")
    assert client.get(f"/sessions/{ana_session_id}", headers=bearer(bia_token)).status_code == 404
    forbidden = client.delete(f"/sessions/{ana_session_id}", headers=bearer(bia_token))
    assert forbidden.status_code == 404

    assert client.get("/sessions", headers=bearer(ana_token)).json()[0]["id"] == ana_session_id