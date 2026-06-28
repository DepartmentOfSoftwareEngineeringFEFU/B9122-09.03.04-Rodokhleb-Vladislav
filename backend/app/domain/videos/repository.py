from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List, Tuple

from ...shared.sql_models import Video
from ...shared.exceptions import NotFoundError


class VideoRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, video_id: int) -> Optional[Video]:
        return self.db.get(Video, video_id)

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Video], int]:
        stmt = select(Video).where(Video.user_id == user_id).offset(skip).limit(limit).order_by(Video.created_at.desc())
        videos = self.db.execute(stmt).scalars().all()

        count_stmt = select(func.count()).select_from(Video).where(Video.user_id == user_id)
        total = self.db.execute(count_stmt).scalar_one()

        return videos, total

    def create(self, user_id: int, filename: str, file_path: str, file_size: int,
               duration: Optional[float] = None) -> Video:
        video = Video(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            duration=duration
        )
        self.db.add(video)
        self.db.flush()
        return video

    def update(self, video_id: int, **kwargs) -> Video:
        video = self.get_by_id(video_id)
        if not video:
            raise NotFoundError(f"Video with id {video_id} not found")

        for key, value in kwargs.items():
            if hasattr(video, key) and value is not None:
                setattr(video, key, value)

        self.db.flush()
        return video

    def delete(self, video_id: int) -> bool:
        video = self.get_by_id(video_id)
        if not video:
            return False

        self.db.delete(video)
        self.db.flush()
        return True

    def exists_by_id(self, video_id: int, user_id: Optional[int] = None) -> bool:
        stmt = select(Video.id).where(Video.id == video_id)
        if user_id:
            stmt = stmt.where(Video.user_id == user_id)
        return self.db.execute(stmt).first() is not None

    def get_user_video_count(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(Video).where(Video.user_id == user_id)
        return self.db.execute(stmt).scalar_one()