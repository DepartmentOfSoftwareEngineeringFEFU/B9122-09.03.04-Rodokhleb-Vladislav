from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io

from .models import UserCreate, UserUpdate, UserResponse, UsersListResponse
from .service import UserService
from ...shared.database import get_db
from ...shared.exceptions import NotFoundError, ValidationError
from ...api.deps import get_current_user_id
from ...config import settings
from ...shared.minio_client import minio_client

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db=db, secret_key=settings.SECRET_KEY)


@router.get("/", response_model=UsersListResponse)
def get_users(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(50, ge=1, le=100, description="Количество записей на странице"),
    user_service: UserService = Depends(get_user_service),
    current_user_id: int = Depends(get_current_user_id)
):
    return user_service.get_users(page=page, size=size)


@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_user(user_id)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return user_service.get_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/me", response_model=UserResponse)
def update_me(
        username: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None),
        user_id: int = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service)
):
    try:
        update_data = {}

        if username:
            update_data['username'] = username

        if avatar:
            file_content = avatar.file.read()
            avatar_path = user_service.upload_avatar(file_content, user_id, avatar.filename)
            update_data['preview_url'] = avatar_path

        return user_service.update_user(user_id, update_data, password=password)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    try:
        user_service.delete_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/me/stats")
def get_me_stats(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.get_user_stats(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/me/avatar")
def get_my_avatar(
        user_id: int = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service)
):
    try:
        user = user_service.repo.get_by_id(user_id)
        if not user or not user.preview_url:
            raise HTTPException(status_code=404, detail="Avatar not found")

        object_name = user.preview_url

        if object_name.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(object_name)
            parts = parsed.path.lstrip('/').split('/', 1)
            if len(parts) > 1:
                object_name = parts[1]

        folder = "avatars"
        if "/" in object_name:
            folder, object_name = object_name.split('/', 1)

        file_data = minio_client.download_file(object_name=object_name, folder=folder)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))