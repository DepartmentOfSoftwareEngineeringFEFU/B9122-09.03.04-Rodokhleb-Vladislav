import os
import uuid
import cv2
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile

from ...config import settings
from ...shared.minio_client import minio_client
from ...shared.exceptions import VideoProcessingError, ValidationError


class VideoHandler:

    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

    def __init__(self):
        self.bucket = settings.MINIO_BUCKET
        self.folder_videos = settings.MINIO_FOLDER_VIDEOS

    def _validate_file(self, filename: str, file_size: int) -> None:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file format. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        max_size_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValidationError(
                f"File too large. Max size: {settings.MAX_VIDEO_SIZE_MB} MB"
            )

    def _generate_unique_filename(self, original_filename: str, user_id: int) -> str:
        ext = os.path.splitext(original_filename)[1].lower()
        unique_id = uuid.uuid4().hex
        return f"user_{user_id}/{unique_id}{ext}"

    def _get_video_info(self, file_path: str) -> dict:

        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video file: {file_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if fps > 0:
            duration = frame_count / fps
        else:
            duration = 0.0

        cap.release()

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count
        }

    def _get_video_info_from_bytes(self, file_bytes: bytes) -> dict:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            info = self._get_video_info(tmp_path)
        finally:
            os.unlink(tmp_path)

        return info

    async def save_video(self, file: UploadFile, user_id: int) -> dict:
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        self._validate_file(file.filename, file_size)

        unique_filename = self._generate_unique_filename(file.filename, user_id)

        print(f"Uploading video to MinIO...")
        print(f"Bucket: {self.bucket}")
        print(f"Folder: {self.folder_videos}")
        print(f"Object: {unique_filename}")

        video_info = self._get_video_info_from_bytes(content)

        try:
            object_key = minio_client.upload_file(
                file_data=content,
                object_name=unique_filename,
                folder=self.folder_videos,
                content_type="video/mp4"
            )
            print(f"Video uploaded successfully: {object_key}")
        except Exception as e:
            print(f"Upload failed: {e}")
            raise VideoProcessingError(f"Failed to upload video to storage: {str(e)}")

        return {
            "filename": file.filename,
            "file_path": object_key,
            "file_size": file_size,
            "duration": video_info["duration"],
            "width": video_info["width"],
            "height": video_info["height"],
            "fps": video_info["fps"],
            "frame_count": video_info["frame_count"]
        }

    def get_video_url(self, file_path: str, expires_in: int = 3600) -> str:
        parts = file_path.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = self.folder_videos
            object_name = file_path
        return minio_client.get_file_url(object_name, folder, expires_in)

    def delete_video(self, file_path: str) -> bool:
        parts = file_path.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = self.folder_videos
            object_name = file_path
        return minio_client.delete_file(object_name, folder)

    def get_video_bytes(self, file_path: str) -> bytes:
        parts = file_path.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = self.folder_videos
            object_name = file_path
        return minio_client.download_file(object_name, folder)

    def video_exists(self, file_path: str) -> bool:
        parts = file_path.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = self.folder_videos
            object_name = file_path
        return minio_client.file_exists(object_name, folder)

    def get_video_info_by_path(self, file_path_key: str) -> dict:

        temp_path = None
        try:
            parts = file_path_key.split('/', 1)
            if len(parts) == 2:
                folder = parts[0]
                object_name = parts[1]
            else:
                folder = self.folder_videos
                object_name = file_path_key

            video_bytes = minio_client.download_file(object_name, folder)

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
                tmp_file.write(video_bytes)
                temp_path = tmp_file.name

            info = self._get_video_info(temp_path)
            return info
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

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
            raise VideoProcessingError(f"Failed to upload avatar: {str(e)}")