"""Endpoint de disponibilidade da API."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Informa que a API está disponível."""
    return {"status": "ok"}
