from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from jose import JWTError, jwt
from passlib.context import CryptContext

from .repository import AuthRepository
from .models import UserResponse, UserRole
from ...shared.exceptions import AuthError, NotFoundError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: Session, secret_key: str, algorithm: str = "HS256",
                 access_token_expire_minutes: int = 15, refresh_token_expire_days: int = 7):
        self.db = db
        self.repo = AuthRepository(db)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _create_token(self, user_id: int, username: str, email: str, role: UserRole, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "role": role.value,
            "exp": expire
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_tokens(self, user_id: int, username: str, email: str, role: UserRole) -> Dict[str, str]:
        access_token = self._create_token(
            user_id, username, email, role,
            timedelta(minutes=self.access_token_expire_minutes)
        )
        refresh_token = self._create_token(
            user_id, username, email, role,
            timedelta(days=self.refresh_token_expire_days)
        )
        return {"access_token": access_token, "refresh_token": refresh_token}

    def register(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> Dict[str, Any]:
        if self.repo.check_username_exists(username):
            raise AuthError("Username already exists")

        if self.repo.check_email_exists(email):
            raise AuthError("Email already exists")

        password_hash = self.hash_password(password)
        user = self.repo.create_user(username, email, password_hash, role)
        self.db.commit()

        tokens = self.create_tokens(user.id, user.username, user.email, user.role)

        return {
            "user": UserResponse.model_validate(user),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        user = self.repo.get_user_by_email(email)

        if not user:
            raise AuthError("Invalid email or password")

        if not self.verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")

        tokens = self.create_tokens(user.id, user.username, user.email, user.role)

        return {
            "user": UserResponse.model_validate(user),
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }

    def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            username = payload.get("username")
            email = payload.get("email")
            role = payload.get("role")

            if not user_id or not username or not email or not role:
                raise AuthError("Invalid refresh token")

            user = self.repo.get_user_by_id(user_id)
            if not user:
                raise AuthError("User not found")

            return self.create_tokens(user_id, username, email, UserRole(role))
        except JWTError as e:
            raise AuthError(f"Invalid refresh token: {str(e)}")

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            username = payload.get("username")
            email = payload.get("email")
            role = payload.get("role")

            if user_id is None or username is None or email is None or role is None:
                raise AuthError("Invalid token payload")

            return {"user_id": user_id, "username": username, "email": email, "role": role}
        except JWTError as e:
            raise AuthError(f"Invalid token: {str(e)}")

    def get_current_user(self, user_id: int) -> Dict[str, Any]:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)

    def is_admin(self, user_id: int) -> bool:
        user = self.repo.get_user_by_id(user_id)
        return user.role == UserRole.ADMIN if user else False