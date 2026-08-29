"""Contratos Pydantic relacionados a usuários."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserAddress(BaseModel):
    """Campos de endereço associados a um usuário."""

    street: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=30)
    complement: str | None = Field(default=None, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=2)
    zip_code: str | None = Field(default=None, min_length=8, max_length=8)


class UserCreate(UserAddress):
    """Dados aceitos no cadastro de uma conta."""

    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Credenciais aceitas para iniciar uma sessão."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(UserAddress):
    """Dados que poderão ser alterados no perfil."""

    name: str | None = Field(default=None, min_length=2, max_length=120)


class UserRead(UserAddress):
    """Dados públicos de uma conta, sem credenciais."""

    id: str
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
