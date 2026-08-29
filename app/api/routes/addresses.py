"""Endpoint interno de consulta de endereços pelo ViaCEP."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Deque

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.schemas.address import AddressRead
from app.services.viacep import (
    AddressNotFoundError,
    InvalidZipCodeError,
    ViaCepService,
    ViaCepUnavailableError,
)

router = APIRouter(prefix="/addresses", tags=["addresses"])


class IpRateLimiter:
    """Limita consultas por IP durante uma janela deslizante em memória."""

    def __init__(self) -> None:
        self._requests: defaultdict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, ip_address: str, limit: int, window_seconds: int) -> bool:
        """Registra uma consulta quando ela ainda está dentro do limite."""
        now = monotonic()
        with self._lock:
            requests = self._requests[ip_address]
            while requests and now - requests[0] >= window_seconds:
                requests.popleft()
            if len(requests) >= limit:
                return False
            requests.append(now)
            return True

    def clear(self) -> None:
        """Remove o histórico; utilizado para isolamento de testes."""
        with self._lock:
            self._requests.clear()


rate_limiter = IpRateLimiter()


@router.get("/lookup/{zip_code}", response_model=AddressRead)
async def lookup_address(zip_code: str, request: Request) -> AddressRead:
    """Consulta um CEP validado, mantendo a chamada externa exclusivamente na API."""
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(
        client_ip,
        settings.viacep_rate_limit_requests,
        settings.viacep_rate_limit_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many address lookup requests. Try again later.",
        )

    try:
        return await ViaCepService(settings).lookup(zip_code)
    except InvalidZipCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CEP must contain 8 digits.") from exc
    except AddressNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found for this CEP.") from exc
    except ViaCepUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Address lookup service is unavailable.",
        ) from exc