from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .models import FragmentResponse, SearchRequestResponse, SearchRequestStatus
from .service import FragmentService
from ...shared.database import get_db
from ...shared.exceptions import NotFoundError
from ...api.deps import get_current_user_id

router = APIRouter(prefix="/fragments", tags=["fragments"])


def get_fragment_service(db: Session = Depends(get_db)) -> FragmentService:
    return FragmentService(db=db)


@router.get("/requests", response_model=dict)
def get_user_requests(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    fragment_service: FragmentService = Depends(get_fragment_service)
):
    return fragment_service.get_user_requests(user_id, page=page, size=size)


@router.get("/requests/{request_id}/status", response_model=SearchRequestStatus)
def get_request_status(
    request_id: int,
    user_id: int = Depends(get_current_user_id),
    fragment_service: FragmentService = Depends(get_fragment_service)
):
    try:
        return fragment_service.get_request_status(request_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/requests/{request_id}", response_model=List[FragmentResponse])
def get_request_fragments(
    request_id: int,
    user_id: int = Depends(get_current_user_id),
    fragment_service: FragmentService = Depends(get_fragment_service)
):
    try:
        return fragment_service.get_fragments_by_request(request_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    user_id: int = Depends(get_current_user_id),
    fragment_service: FragmentService = Depends(get_fragment_service)
):
    try:
        fragment_service.delete_request(request_id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{fragment_id}", response_model=FragmentResponse)
def get_fragment(
    fragment_id: int,
    fragment_service: FragmentService = Depends(get_fragment_service)
):
    try:
        return fragment_service.get_fragment(fragment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))