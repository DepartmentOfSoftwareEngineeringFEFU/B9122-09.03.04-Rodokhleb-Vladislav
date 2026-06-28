from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..shared.database import get_db
from ..shared.exceptions import AuthError


security = HTTPBearer(auto_error=False)


def get_current_user_id(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
) -> int:

    from ..domain.auth.service import AuthService

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        auth_service = AuthService(db)
        payload = auth_service.verify_token(credentials.credentials)
        return payload.get("user_id")
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )