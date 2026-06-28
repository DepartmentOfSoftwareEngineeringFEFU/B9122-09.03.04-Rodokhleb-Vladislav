from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class VideoServiceInterface(ABC):

    @abstractmethod
    async def upload_video(self, user_id: int, file_data: bytes, filename: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_video(self, video_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_user_videos(self, user_id: int, page: int, size: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_video(self, video_id: int, user_id: int) -> bool:
        pass