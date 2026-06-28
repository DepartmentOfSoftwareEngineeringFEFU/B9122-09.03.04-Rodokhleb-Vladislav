from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List, Tuple

from ...shared.sql_models import User
from ...shared.exceptions import NotFoundError


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[User], int]:
        stmt = select(User).offset(skip).limit(limit).order_by(User.id)
        users = self.db.execute(stmt).scalars().all()

        count_stmt = select(func.count()).select_from(User)
        total = self.db.execute(count_stmt).scalar_one()

        return users, total

    def create(self, username: str, password_hash: str) -> User:
        user = User(
            username=username.lower(),
            password_hash=password_hash
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user_id: int, **kwargs) -> User:
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.db.flush()
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.flush()
        return True

    def exists_by_username(self, username: str) -> bool:
        stmt = select(User.id).where(User.username == username.lower())
        return self.db.execute(stmt).first() is not None

    def exists_by_id(self, user_id: int) -> bool:
        return self.db.get(User, user_id) is not None