"""Testes de emissão e autenticação de chaves de API."""

from fastapi.testclient import TestClient

from app.db.models.api_key import ApiKey
from tests.test_authentication_flows import bearer, client, login, register


def test_api_key_is_returned_once_and_listing_excludes_credential_material(client: TestClient) -> None:
    """A resposta de criação inclui segredo; modelo e listagem não o expõem."""
    register(client)
    token = login(client)

    created = client.post("/api-keys", headers=bearer(token), json={"name": "Integração local"})

    assert created.status_code == 201
    payload = created.json()
    assert payload["secret"]
    assert payload["public_key_id"].startswith("ilk_")
    assert not hasattr(ApiKey, "secret")
    listed = client.get("/api-keys", headers=bearer(token))
    assert listed.status_code == 200
    assert listed.json() == [{key: value for key, value in payload.items() if key != "secret"}]
    assert "secret_hash" not in listed.text
    assert payload["secret"] not in listed.text


def test_api_key_login_issues_bearer_token_that_reads_profile(client: TestClient) -> None:
    register(client)
    token = login(client)
    key = client.post("/api-keys", headers=bearer(token), json={"name": "Automação"}).json()

    exchange = client.post("/auth/api-key-login", json={"key_id": key["public_key_id"], "secret": key["secret"]})

    assert exchange.status_code == 200
    profile = client.get("/users/me", headers=bearer(exchange.json()["access_token"]))
    assert profile.status_code == 200
    assert profile.json()["email"] == "ana@example.com"
    assert client.get("/api-keys", headers=bearer(token)).json()[0]["last_used_at"] is not None


def test_api_key_login_rejects_invalid_and_revoked_credentials(client: TestClient) -> None:
    register(client)
    token = login(client)
    key = client.post("/api-keys", headers=bearer(token), json={"name": "Temporária"}).json()

    assert client.post("/auth/api-key-login", json={"key_id": key["public_key_id"], "secret": "wrong"}).status_code == 401
    assert client.post("/auth/api-key-login", json={"key_id": "ilk_unknown", "secret": key["secret"]}).status_code == 401
    assert client.delete(f"/api-keys/{key['id']}", headers=bearer(token)).status_code == 204
    assert client.post("/auth/api-key-login", json={"key_id": key["public_key_id"], "secret": key["secret"]}).status_code == 401