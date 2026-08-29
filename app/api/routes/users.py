"""Endpoints do perfil do usuário autenticado."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserRead, UserUpdate
from app.services.users import update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Retorna o perfil da conta autenticada."""
    return current_user


@router.put("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Atualiza o perfil da conta autenticada."""
    return update_user(db, current_user, payload)