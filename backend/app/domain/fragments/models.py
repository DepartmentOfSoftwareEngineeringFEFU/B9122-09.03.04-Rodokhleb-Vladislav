from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class FragmentBase(BaseModel):

    keywords: Optional[List[str]] = None
    start_frame: int
    end_frame: int
    storage_path: str


class FragmentCreate(FragmentBase):
    request_id: int


class FragmentResponse(FragmentBase):
    id: int
    request_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequestBase(BaseModel):
    user_id: int
    video_id: int
    keywords: Dict[str, str]
    status: str = "pending"


class SearchRequestCreate(SearchRequestBase):
    pass


class SearchRequestResponse(SearchRequestBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchRequestStatus(BaseModel):
    request_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None