from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from ...shared.sql_models import User, UserRole
from ...shared.exceptions import NotFoundError


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def create_user(self, username: str, email: str, password_hash: str, role: UserRole = UserRole.USER) -> User:
        user = User(
            username=username.lower(),
            email=email.lower(),
            password_hash=password_hash,
            role=role
        )
        self.db.add(user)
        self.db.flush()
        return user

    def check_email_exists(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email.lower())
        return self.db.execute(stmt).first() is not None

    def check_username_exists(self, username: str) -> bool:
        stmt = select(User.id).where(User.username == username.lower())
        return self.db.execute(stmt).first() is not None