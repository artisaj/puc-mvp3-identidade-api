"""Testes da consulta de CEP e da proteção contra abuso por IP."""

from collections.abc import Generator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes.addresses import rate_limiter
from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    """Fornece um cliente sem histórico de limitação entre testes."""
    monkeypatch.setenv("VIACEP_RATE_LIMIT_REQUESTS", "10")
    get_settings.cache_clear()
    rate_limiter.clear()
    with TestClient(app) as test_client:
        yield test_client
    rate_limiter.clear()
    get_settings.cache_clear()


def viacep_response(payload: dict[str, object]) -> httpx.Response:
    """Monta uma resposta HTTPX válida para as simulações do provedor."""
    request = httpx.Request("GET", "https://viacep.com.br/ws/01001000/json/")
    return httpx.Response(200, json=payload, request=request)


def test_lookup_normalizes_cep_and_address(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A rota normaliza o CEP e os campos retornados pelo ViaCEP."""
    get = AsyncMock(
        return_value=viacep_response(
            {
                "cep": "01001-000",
                "logradouro": " Praça da Sé ",
                "complemento": "lado ímpar",
                "bairro": "Sé",
                "localidade": "São Paulo",
                "uf": "SP",
            }
        )
    )
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    response = client.get("/addresses/lookup/01001-000")

    assert response.status_code == 200
    assert response.json() == {
        "zip_code": "01001000",
        "street": "Praça da Sé",
        "complement": "lado ímpar",
        "neighborhood": "Sé",
        "city": "São Paulo",
        "state": "SP",
    }
    assert get.await_args.args[0].endswith("/01001000/json/")


def test_lookup_rejects_invalid_cep_without_calling_provider(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """CEP inválido recebe erro claro e não inicia chamada de rede."""
    get = AsyncMock()
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    response = client.get("/addresses/lookup/123")

    assert response.status_code == 400
    assert response.json()["detail"] == "CEP must contain 8 digits."
    get.assert_not_awaited()


def test_lookup_returns_not_found_for_viacep_erro_flag(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A sinalização de CEP inexistente do ViaCEP é convertida em 404."""
    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(return_value=viacep_response({"erro": True})))

    response = client.get("/addresses/lookup/99999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Address not found for this CEP."


def test_lookup_returns_service_unavailable_for_httpx_failure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Falhas de transporte do provedor são isoladas como indisponibilidade."""
    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=httpx.TimeoutException("timed out")))

    response = client.get("/addresses/lookup/01001000")

    assert response.status_code == 503
    assert response.json()["detail"] == "Address lookup service is unavailable."


def test_lookup_limits_requests_per_ip(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A décima primeira consulta na janela é bloqueada para o mesmo IP."""
    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(return_value=viacep_response({})))

    for _ in range(10):
        assert client.get("/addresses/lookup/01001000").status_code == 200

    response = client.get("/addresses/lookup/01001000")

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many address lookup requests. Try again later."