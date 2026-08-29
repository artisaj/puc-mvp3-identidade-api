"""Endpoints para administrar as sessões do usuário autenticado."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.session import UserSession
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.session import SessionRead
from app.services.sessions import list_active_sessions, revoke_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionRead])
def read_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[UserSession]:
    """Lista exclusivamente as sessões ativas da conta autenticada."""
    return list_active_sessions(db, current_user.id)


@router.get("/{session_id}", response_model=SessionRead)
def read_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSession:
    """Retorna uma sessão pertencente exclusivamente à conta autenticada."""
    session = db.get(UserSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Revoga uma sessão que pertença à conta autenticada."""
    session = db.get(UserSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    revoke_session(db, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)