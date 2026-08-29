"""Contratos de consulta de endereços."""

from pydantic import BaseModel, Field


class AddressRead(BaseModel):
    """Endereço normalizado retornado pela consulta de CEP."""

    zip_code: str = Field(pattern=r"^\d{8}$")
    street: str | None = Field(default=None, max_length=255)
    complement: str | None = Field(default=None, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)