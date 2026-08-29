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
    payload = decode_token(token)
    if payload.get("purpose") is not None:
        raise jwt.InvalidTokenError("Token purpose is invalid")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("Token subject is invalid")
    return subject


def password_hash_fingerprint(password_hash: str) -> str:
    """Cria uma impressão do hash atual sem incluir credenciais no JWT."""
    return sha256(password_hash.encode("utf-8")).hexdigest()


def create_password_reset_token(subject: str, password_hash: str) -> str:
    """Cria um JWT curto, restrito à redefinição da senha atual do usuário."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured")

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)
    payload = {
        "sub": subject,
        "purpose": "password_reset",
        "password_fingerprint": password_hash_fingerprint(password_hash),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> tuple[str, str]:
    """Valida o propósito de um JWT de reset e retorna sujeito e impressão."""
    payload = decode_token(token)
    subject = payload.get("sub")
    fingerprint = payload.get("password_fingerprint")
    if (
        payload.get("purpose") != "password_reset"
        or not isinstance(subject, str)
        or not subject
        or not isinstance(fingerprint, str)
        or not fingerprint
    ):
        raise jwt.InvalidTokenError("Password reset token is invalid")
    return subject, fingerprint


def decode_token(token: str) -> dict[str, object]:
    """Valida assinatura e expiração de um JWT e retorna suas claims."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured")

    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])


def generate_refresh_token() -> str:
    """Gera um token opaco de alta entropia para renovação de sessão."""
    return token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Calcula o hash persistível de um refresh token sem armazená-lo em claro."""
    return sha256(token.encode("utf-8")).hexdigest()


def verify_refresh_token(token: str, token_hash: str) -> bool:
    """Compara um refresh token com seu hash de modo seguro."""
    return compare_digest(hash_refresh_token(token), token_hash)
