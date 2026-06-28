from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..shared.database import get_db
from ..shared.exceptions import AuthError
from ..config import settings
from ..domain.auth.service import AuthService

security = HTTPBearer(auto_error=False)


def get_current_user_id(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
) -> int:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    auth_service = AuthService(
        db=db,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    try:
        payload = auth_service.verify_token(credentials.credentials)
        return payload["user_id"]
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )