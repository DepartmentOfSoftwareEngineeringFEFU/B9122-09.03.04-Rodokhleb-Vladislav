from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')

class BaseModel(PydanticBaseModel):

    class Config:
        from_attributes = True

class ResponseModel(BaseModel, Generic[T]):

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int