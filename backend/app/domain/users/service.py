import uuid

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import os
from .repository import UserRepository
from .models import UserResponse, UserCreate, UserUpdate, UsersListResponse
from ..videos import VideoHandler
from ...shared.exceptions import NotFoundError, ValidationError
from ...domain.auth.service import AuthService
from ...shared.minio_client import minio_client


class UserService:

    def __init__(self, db: Session, secret_key: str = None):
        self.db = db
        self.repo = UserRepository(db)
        self.secret_key = secret_key
        self.handler = VideoHandler()

    def _hash_password(self, password: str) -> str:
        return AuthService.hash_password(password)

    def upload_avatar(self, file_data: bytes, user_id: int, original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            ext = '.jpg'

        unique_id = uuid.uuid4().hex
        object_name = f"user_{user_id}/{unique_id}{ext}"

        try:
            full_key = minio_client.upload_file(
                file_data=file_data,
                object_name=object_name,
                folder="avatars",
                content_type=f"image/{ext.lstrip('.')}"
            )
            return full_key

        except Exception as e:
            raise ValidationError(f"Failed to upload avatar: {str(e)}")

    def _get_avatar_url(self, preview_url: Optional[str]) -> Optional[str]:
        if not preview_url:
            return None
        parts = preview_url.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = "avatars"
            object_name = preview_url
        try:
            return minio_client.get_file_url(object_name, folder, expires_in=3600)
        except Exception:
            return None

    def get_user(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")
        response = UserResponse.model_validate(user)
        response.avatar_url = self._get_avatar_url(user.preview_url)
        return response

    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        return UserResponse.model_validate(user)

    def get_users(self, page: int = 1, size: int = 50) -> UsersListResponse:
        skip = (page - 1) * size
        users, total = self.repo.get_all(skip=skip, limit=size)
        items = []
        for user in users:
            resp = UserResponse.model_validate(user)
            resp.avatar_url = self._get_avatar_url(user.preview_url)
            items.append(resp)
        return UsersListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def create_user(self, user_data: UserCreate) -> UserResponse:
        if self.repo.exists_by_username(user_data.username):
            raise ValidationError(f"Username '{user_data.username}' already exists")

        password_hash = self._hash_password(user_data.password)
        user = self.repo.create(user_data.username, password_hash)
        self.db.commit()

        return UserResponse.model_validate(user)

    def update_user(self, user_id: int, update_data: dict, password: Optional[str] = None) -> UserResponse:
        if not self.repo.exists_by_id(user_id):
            raise NotFoundError(f"User with id {user_id} not found")

        db_updates = {}

        if 'username' in update_data and update_data['username']:
            if self.repo.exists_by_username(update_data['username']):
                raise ValidationError(f"Username '{update_data['username']}' already exists")
            db_updates["username"] = update_data['username'].lower()

        if 'preview_url' in update_data and update_data['preview_url']:
            db_updates["preview_url"] = update_data['preview_url']

        if password:
            db_updates["password_hash"] = self._hash_password(password)

        if db_updates:
            user = self.repo.update(user_id, **db_updates)
            self.db.commit()
        else:
            user = self.repo.get_by_id(user_id)

        response = UserResponse.model_validate(user)
        response.avatar_url = self._get_avatar_url(user.preview_url)
        return response

    def delete_user(self, user_id: int) -> bool:
        if not self.repo.exists_by_id(user_id):
            raise NotFoundError(f"User with id {user_id} not found")

        result = self.repo.delete(user_id)
        self.db.commit()
        return result

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        from ...shared.sql_models import Video, SearchRequest

        if not self.repo.exists_by_id(user_id):
            raise NotFoundError(f"User with id {user_id} not found")

        videos_count = self.db.query(Video).filter(Video.user_id == user_id).count()

        requests_count = self.db.query(SearchRequest).filter(SearchRequest.user_id == user_id).count()

        return {
            "user_id": user_id,
            "videos_count": videos_count,
            "search_requests_count": requests_count
        }

