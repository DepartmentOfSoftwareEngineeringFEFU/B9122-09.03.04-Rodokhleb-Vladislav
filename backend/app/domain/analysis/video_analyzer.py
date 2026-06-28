from typing import List, Dict, Any, Optional
from .service import AnalysisService
from .models import AnalysisResult
from ...shared.minio_client import minio_client
from ...config import settings


class VideoAnalyzer:

    def __init__(self, verbose: bool = True):
        self.service = AnalysisService(verbose=verbose)

    def analyze_video_from_minio(
        self,
        video_key: str,
        keywords: List[str],
        fps: int = 2,
        confidence: float = 0.35,
        progress_callback: Optional[callable] = None,
        request_id: Optional[int] = None
    ) -> AnalysisResult:

        return self.service.analyze_video(
            video_path_key=video_key,
            keywords=keywords,
            fps=fps,
            confidence=confidence,
            progress_callback=progress_callback,
            request_id=request_id
        )

    def get_fragment_url(self, fragment_key: str, expires_in: int = 3600) -> str:
        return minio_client.get_file_url(
            object_name=fragment_key,
            folder=settings.MINIO_FOLDER_FRAGMENTS,
            expires_in=expires_in
        )