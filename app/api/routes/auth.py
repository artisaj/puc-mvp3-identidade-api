"""Endpoints de autenticação."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.session import TokenRead
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.sessions import (
    create_session,
    get_valid_session_by_refresh_token,
    revoke_session,
    rotate_refresh_token,
)
from app.services.users import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Cria uma conta quando o e-mail ainda não estiver cadastrado."""
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail already registered")
    return create_user(db, payload)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Envia o refresh token sem torná-lo acessível ao JavaScript."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=get_settings().app_env.lower() == "production",
        samesite="lax",
        max_age=get_settings().refresh_token_expire_days * 24 * 60 * 60,
        path="/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove o cookie de refresh no mesmo caminho usado para defini-lo."""
    response.delete_cookie(key="refresh_token", path="/auth", httponly=True, samesite="lax")


@router.post("/login", response_model=TokenRead)
def login(payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenRead:
    """Valida credenciais, cria uma sessão e emite um access token."""
    user = get_user_by_email(db, payload.email)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _, refresh_token = create_session(db, user.id, request.headers.get("user-agent"))
    set_refresh_cookie(response, refresh_token)
    return TokenRead(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenRead)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> TokenRead:
    """Rotaciona um refresh token válido e emite novo JWT de acesso."""
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    session = get_valid_session_by_refresh_token(db, refresh_token)
    if session is None or not session.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_refresh_token = rotate_refresh_token(db, session)
    set_refresh_cookie(response, new_refresh_token)
    return TokenRead(access_token=create_access_token(session.user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """Revoga a sessão indicada pelo refresh token e remove seu cookie."""
    if refresh_token is not None:
        session = get_valid_session_by_refresh_token(db, refresh_token)
        if session is not None:
            revoke_session(db, session)
    clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
