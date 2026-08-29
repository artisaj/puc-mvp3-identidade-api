"""Testes do endpoint de disponibilidade."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    """O serviço deve responder que está disponível."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
