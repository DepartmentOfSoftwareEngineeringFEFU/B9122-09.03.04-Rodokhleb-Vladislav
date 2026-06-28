import enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, ARRAY, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..shared.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    preview_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    search_requests = relationship("SearchRequest", back_populates="user", cascade="all, delete-orphan")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # bytes
    duration = Column(Float)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="videos")
    search_requests = relationship("SearchRequest", back_populates="video")


class SearchRequest(Base):
    __tablename__ = "search_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    keywords = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="search_requests")
    video = relationship("Video", back_populates="search_requests")
    fragments = relationship("Fragment", back_populates="search_request", cascade="all, delete-orphan")


class Fragment(Base):
    __tablename__ = "fragments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("search_requests.id", ondelete="CASCADE"), nullable=False)
    keywords = Column(JSON, nullable=True)
    start_frame = Column(Integer, nullable=False)  # номер начального кадра
    end_frame = Column(Integer, nullable=False)  # номер конечного кадра
    storage_path = Column(String(500), nullable=False)  # путь в MinIO
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    search_request = relationship("SearchRequest", back_populates="fragments")