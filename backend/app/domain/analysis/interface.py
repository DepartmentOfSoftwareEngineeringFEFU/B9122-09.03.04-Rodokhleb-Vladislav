from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AnalysisServiceInterface(ABC):

    @abstractmethod
    def analyze_video(
            self,
            video_path: str,
            keywords: List[str],
            with_detection: bool = False
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze_frame(
            self,
            frame_bytes: bytes,
            keywords: List[str],
            with_detection: bool = False
    ) -> Dict[str, Any]:
        pass