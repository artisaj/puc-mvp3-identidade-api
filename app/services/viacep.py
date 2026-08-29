"""Cliente assíncrono e normalizador da integração ViaCEP."""

import re
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.address import AddressRead


class InvalidZipCodeError(ValueError):
    """Indica que o CEP informado não possui um formato aceito."""


class AddressNotFoundError(LookupError):
    """Indica que o ViaCEP não encontrou o CEP solicitado."""


class ViaCepUnavailableError(RuntimeError):
    """Indica uma falha de comunicação ou resposta inválida do ViaCEP."""


def normalize_zip_code(zip_code: str) -> str:
    """Aceita CEP com ou sem hífen e retorna os oito dígitos."""
    value = zip_code.strip()
    if not re.fullmatch(r"\d{5}-?\d{3}", value):
        raise InvalidZipCodeError("CEP must contain 8 digits")
    return value.replace("-", "")


def _optional_text(value: Any) -> str | None:
    """Converte campos vazios enviados pelo provedor em valores nulos."""
    if not isinstance(value, str):
        return None
    return value.strip() or None


class ViaCepService:
    """Consulta o ViaCEP sem expor o serviço externo aos consumidores da API."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.viacep_base_url.rstrip("/")
        self._timeout = settings.viacep_timeout_seconds

    async def lookup(self, zip_code: str) -> AddressRead:
        """Obtém e normaliza o endereço associado ao CEP informado."""
        normalized_zip_code = normalize_zip_code(zip_code)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/{normalized_zip_code}/json/")
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ViaCepUnavailableError("ViaCEP request failed") from exc

        if not isinstance(payload, dict):
            raise ViaCepUnavailableError("ViaCEP returned an invalid response")
        if payload.get("erro") is True:
            raise AddressNotFoundError("CEP not found")

        return AddressRead(
            zip_code=normalized_zip_code,
            street=_optional_text(payload.get("logradouro")),
            complement=_optional_text(payload.get("complemento")),
            neighborhood=_optional_text(payload.get("bairro")),
            city=_optional_text(payload.get("localidade")),
            state=_optional_text(payload.get("uf")),
        )