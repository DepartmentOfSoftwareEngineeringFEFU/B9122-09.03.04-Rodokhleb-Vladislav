from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .models import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from .service import AuthService
from ...shared.database import get_db
from ...shared.exceptions import AuthError, NotFoundError
from ...config import settings
from ...api.deps import get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(
        db=db,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7
    )


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        result = auth_service.register(
            request.username,
            request.email,
            request.password,
            request.role
        )
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"]
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        result = auth_service.login(
            email=request.email,
            password=request.password
        )
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"]
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        result = auth_service.refresh_tokens(request.refresh_token)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"]
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(
        db=db,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    try:
        return auth_service.get_current_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))