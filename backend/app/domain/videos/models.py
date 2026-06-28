from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import os


class VideoBase(BaseModel):
    filename: str
    file_size: Optional[int] = None
    duration: Optional[float] = None

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("Filename must be between 1 and 255 characters")
        return v


class VideoCreate(BaseModel):
    filename: str
    file_path: str
    file_size: int
    duration: Optional[float] = None


class VideoResponse(VideoBase):
    id: int
    user_id: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class VideoUploadResponse(BaseModel):
    video_id: int
    filename: str
    file_size: int
    message: str = "Video uploaded successfully"


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    page: int
    size: int
    pages: int


class VideoInfo(BaseModel):
    duration: float
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None