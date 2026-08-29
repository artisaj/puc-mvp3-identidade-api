"""Contratos para o fluxo de redefinição de senha."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    """E-mail recebido sem revelar se há uma conta correspondente."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Resposta uniforme; o token só é incluído no ambiente de desenvolvimento."""

    accepted: Literal[True] = True
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    """Token temporário e nova senha para concluir a redefinição."""

    token: str = Field(min_length=1, max_length=4096)
    new_password: str = Field(min_length=8, max_length=128)