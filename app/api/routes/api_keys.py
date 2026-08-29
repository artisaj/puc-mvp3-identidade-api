"""Endpoints autenticados para administrar chaves de API."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.api_key import ApiKey
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyRead
from app.services.api_keys import create_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyCreated:
    """Emite uma chave para a conta autenticada e revela o segredo apenas agora."""
    key, secret = create_api_key(db, current_user, payload)
    metadata = ApiKeyRead.model_validate(key, from_attributes=True)
    return ApiKeyCreated(**metadata.model_dump(), secret=secret)


@router.get("", response_model=list[ApiKeyRead])
def read_keys(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ApiKey]:
    """Lista metadados das chaves da própria conta, sem segredos nem hashes."""
    return list_api_keys(db, current_user.id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Revoga uma chave da própria conta, sem permitir acesso entre usuários."""
    key = db.get(ApiKey, key_id)
    if key is None or key.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    revoke_api_key(db, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)