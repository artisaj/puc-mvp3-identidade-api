"""Dependências compartilhadas para rotas protegidas."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.services.users import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Valida o JWT Bearer e retorna somente uma conta ativa."""
    if credentials is None:
        raise credentials_exception
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise credentials_exception from None

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user