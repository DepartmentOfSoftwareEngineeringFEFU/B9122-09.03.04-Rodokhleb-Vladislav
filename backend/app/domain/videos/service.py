from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import UploadFile

from .repository import VideoRepository
from .video_handler import VideoHandler
from .models import VideoResponse, VideoListResponse, VideoInfo, VideoUploadResponse
from ...shared.exceptions import NotFoundError, VideoProcessingError
from ...config import settings


class VideoService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = VideoRepository(db)
        self.handler = VideoHandler()

    async def upload_video(self, user_id: int, file: UploadFile) -> VideoUploadResponse:

        saved_video = await self.handler.save_video(file, user_id)

        video = self.repo.create(
            user_id=user_id,
            filename=saved_video["filename"],
            file_path=saved_video["file_path"],
            file_size=saved_video["file_size"],
            duration=saved_video["duration"]
        )

        self.db.commit()

        return VideoUploadResponse(
            video_id=video.id,
            filename=video.filename,
            file_size=video.file_size
        )

    def get_video(self, video_id: int, user_id: Optional[int] = None) -> VideoResponse:
        video = self.repo.get_by_id(video_id)

        if not video:
            raise NotFoundError(f"Video with id {video_id} not found")

        if user_id and video.user_id != user_id:
            raise NotFoundError(f"Video with id {video_id} not found")

        return VideoResponse.model_validate(video)

    def get_user_videos(self, user_id: int, page: int = 1, size: int = 50) -> VideoListResponse:
        skip = (page - 1) * size
        videos, total = self.repo.get_by_user_id(user_id, skip=skip, limit=size)

        return VideoListResponse(
            items=[VideoResponse.model_validate(v) for v in videos],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    def delete_video(self, video_id: int, user_id: int) -> bool:
        video = self.repo.get_by_id(video_id)

        if not video:
            raise NotFoundError(f"Video with id {video_id} not found")

        if video.user_id != user_id:
            raise NotFoundError(f"Video with id {video_id} not found")

        self.handler.delete_video(video.file_path)

        result = self.repo.delete(video_id)
        self.db.commit()

        return result

    def get_video_info(self, video_id: int, user_id: int) -> VideoInfo:
        video = self.repo.get_by_id(video_id)

        if not video or video.user_id != user_id:
            raise NotFoundError(f"Video with id {video_id} not found")

        try:
            info = self.handler.get_video_info_by_path(video.file_path)

            return VideoInfo(
                duration=info.get("duration", video.duration or 0),
                file_size=video.file_size,
                width=info.get("width"),
                height=info.get("height"),
                fps=info.get("fps"),
                frame_count=info.get("frame_count")
            )
        except Exception as e:
            print(f"Warning: Could not get video info from MinIO: {e}")
            return VideoInfo(
                duration=video.duration or 0,
                file_size=video.file_size,
                width=None,
                height=None,
                fps=None,
                frame_count=None
            )

    def get_video_path(self, video_id: int, user_id: int) -> str:
        video = self.repo.get_by_id(video_id)

        if not video or video.user_id != user_id:
            raise NotFoundError(f"Video with id {video_id} not found")

        return video.file_path

    def get_video_url(self, video_id: int, user_id: int, expires_in: int = 3600) -> str:
        video = self.repo.get_by_id(video_id)

        if not video or video.user_id != user_id:
            raise NotFoundError(f"Video with id {video_id} not found")

        return self.handler.get_video_url(video.file_path, expires_in)