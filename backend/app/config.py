from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):

    AUTH_MODE: str = "local"
    AUTH_SERVICE_URL: str = "http://auth:8001"

    ANALYSIS_MODE: str = "local"
    ANALYSIS_SERVICE_URL: str = "http://analysis:8002"

    STORAGE_MODE: str = "local"
    STORAGE_SERVICE_URL: str = "http://storage:8003"

    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/db"

    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Внутренний адрес для подключения из контейнера
    MINIO_ENDPOINT: str = "minio:9000"
    # Внешний адрес для генерации ссылок для браузера
    MINIO_EXTERNAL_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "admin1234"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "video-analytics"
    MINIO_FOLDER_VIDEOS: str = "videos"
    MINIO_FOLDER_ANALYTIC_VIDEOS: str = "analytic-videos"
    MINIO_FOLDER_FRAGMENTS: str = "fragments"

    UPLOAD_DIR: str = "data/uploads"
    MAX_VIDEO_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    FRAMES_PER_SECOND: int = 10
    DEFAULT_GAP_THRESHOLD: float = 0.5
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.35
    CLASSIFICATION_CONFIDENCE_THRESHOLD: float = 0.5

    GROUNDING_DINO_MODEL_PATH: str = "models/classifier_model"

    DEBUG: bool = True

    class Config:
        env_file = ".environment"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def ensure_directories():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("models/detectors", exist_ok=True)
    os.makedirs("models/classifiers", exist_ok=True)
    os.makedirs("data", exist_ok=True)


ensure_directories()