from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from .models import VideoResponse, VideoListResponse, VideoInfo, VideoUploadResponse
from .service import VideoService
from ...shared.database import get_db
from ...shared.exceptions import NotFoundError, ValidationError, VideoProcessingError
from ...api.deps import get_current_user_id
from ...config import settings

router = APIRouter(prefix="/videos", tags=["videos"])


def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    return VideoService(db=db)


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    try:
        result = await video_service.upload_video(user_id, file)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except VideoProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=VideoListResponse)
def get_user_videos(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(50, ge=1, le=100, description="Количество записей на странице"),
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    return video_service.get_user_videos(user_id, page=page, size=size)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    try:
        return video_service.get_video(video_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{video_id}/info", response_model=VideoInfo)
def get_video_info(
    video_id: int,
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    try:
        return video_service.get_video_info(video_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    try:
        video_service.delete_video(video_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VideoProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{video_id}/url")
def get_video_url(
    video_id: int,
    expires_in: int = 3600,
    user_id: int = Depends(get_current_user_id),
    video_service: VideoService = Depends(get_video_service)
):
    try:
        video = video_service.get_video(video_id, user_id)
        url = video_service.handler.get_video_url(video.file_path, expires_in)
        return {"url": url, "expires_in": expires_in}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))