from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class UserServiceInterface(ABC):


    @abstractmethod
    def get_user(self, user_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_users(self, page: int, size: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        pass