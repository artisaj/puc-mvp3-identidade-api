"""Regras de persistência de usuários."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Busca um usuário pelo e-mail normalizado."""
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Busca uma conta pelo identificador persistido no JWT."""
    return db.get(User, user_id)


def create_user(db: Session, payload: UserCreate) -> User:
    """Cria uma conta com a senha persistida exclusivamente como hash."""
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        street=payload.street,
        number=payload.number,
        complement=payload.complement,
        neighborhood=payload.neighborhood,
        city=payload.city,
        state=payload.state,
        zip_code=payload.zip_code,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """Atualiza somente os campos explicitamente enviados pelo usuário."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
