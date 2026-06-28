from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AuthServiceInterface(ABC):


    @abstractmethod
    def register(self, username: str, password: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def login(self, username: str, password: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_current_user(self, user_id: int) -> Dict[str, Any]:
        pass