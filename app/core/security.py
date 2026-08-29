"""Primitivas de segurança para credenciais e tokens."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

ALGORITHM = "HS256"
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Gera um hash Argon2 para uma senha."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica uma senha contra o hash Argon2 persistido."""
    return password_hasher.verify(password, password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Cria um JWT de acesso assinado e com expiração."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured")

    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Valida um JWT e retorna o identificador do usuário autenticado."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured")

    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("Token subject is invalid")
    return subject


def generate_refresh_token() -> str:
    """Gera um token opaco de alta entropia para renovação de sessão."""
    return token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Calcula o hash persistível de um refresh token sem armazená-lo em claro."""
    return sha256(token.encode("utf-8")).hexdigest()


def verify_refresh_token(token: str, token_hash: str) -> bool:
    """Compara um refresh token com seu hash de modo seguro."""
    return compare_digest(hash_refresh_token(token), token_hash)
