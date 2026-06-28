from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Any, Dict
from datetime import datetime
from enum import Enum


class Detection(BaseModel):
    bbox: Tuple[float, float, float, float]
    confidence: float
    label: str


class FrameAnalysis(BaseModel):
    timestamp: float
    frame_index: int
    present_keywords: List[str] = []
    detections: List[Detection] = []
    has_objects: bool = False


class Fragment(BaseModel):
    keyword: str
    start_time: float
    end_time: float
    preview_bytes: Optional[bytes] = None
    detections: List[Detection] = []
    frame_count: int = 0


class AnalysisRequest(BaseModel):
    keywords: List[str] = Field(..., min_length=1, description="Список ключевых слов для поиска")
    fps: int = Field(2, ge=1, le=30, description="Количество кадров в секунду для анализа")
    confidence: float = Field(0.35, ge=0.05, le=0.9, description="Порог уверенности детекции")


class AnalysisResult(BaseModel):
    fragments: List[Fragment]
    total_frames_analyzed: int
    duration: float
    keywords_found: List[str]
    with_detection: bool = True


class AnalysisStatus(BaseModel):
    request_id: int
    status: str
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None