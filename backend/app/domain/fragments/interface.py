from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class FragmentServiceInterface(ABC):

    @abstractmethod
    def create_request(self, user_id: int, video_id: int, keywords: List[str], with_detection: bool) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_request_status(self, request_id: int, user_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_fragments(self, request_id: int, fragments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_fragments_by_request(self, request_id: int, user_id: int) -> List[Dict[str, Any]]:
        pass