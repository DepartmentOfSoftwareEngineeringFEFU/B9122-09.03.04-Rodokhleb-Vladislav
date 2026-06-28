from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List, Tuple, Dict
import json

from ...shared.sql_models import SearchRequest, Fragment
from ...shared.exceptions import NotFoundError


class FragmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_request(
            self,
            user_id: int,
            video_id: int,
            keywords: dict
    ) -> SearchRequest:
        search_request = SearchRequest(
            user_id=user_id,
            video_id=video_id,
            keywords=keywords,
            status="pending"
        )
        self.db.add(search_request)
        self.db.flush()
        return search_request

    def get_request(self, request_id: int, user_id: Optional[int] = None) -> Optional[SearchRequest]:
        stmt = select(SearchRequest).where(SearchRequest.id == request_id)
        if user_id:
            stmt = stmt.where(SearchRequest.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_requests_by_user(
            self,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[SearchRequest], int]:
        stmt = select(SearchRequest).where(
            SearchRequest.user_id == user_id
        ).offset(skip).limit(limit).order_by(SearchRequest.created_at.desc())

        requests = self.db.execute(stmt).scalars().all()

        count_stmt = select(func.count()).select_from(SearchRequest).where(
            SearchRequest.user_id == user_id
        )
        total = self.db.execute(count_stmt).scalar_one()

        return requests, total

    def update_request_status(
            self,
            request_id: int,
            status: str
    ) -> SearchRequest:
        search_request = self.get_request(request_id)
        if not search_request:
            raise NotFoundError(f"SearchRequest with id {request_id} not found")

        search_request.status = status

        if status == "completed" or status == "error":
            from datetime import datetime
            search_request.completed_at = datetime.now()

        self.db.flush()
        return search_request

    def delete_request(self, request_id: int) -> bool:
        search_request = self.get_request(request_id)
        if not search_request:
            return False

        self.db.delete(search_request)
        self.db.flush()
        return True

    def create_fragment(
            self,
            request_id: int,
            keywords: list,
            start_frame: int,
            end_frame: int,
            storage_path: str
    ) -> Fragment:
        fragment = Fragment(
            request_id=request_id,
            keywords=keywords,
            start_frame=start_frame,
            end_frame=end_frame,
            storage_path=storage_path
        )
        self.db.add(fragment)
        self.db.flush()
        return fragment

    def create_fragments_batch(self, fragments_data: List[dict]) -> List[Fragment]:
        fragments = []
        for data in fragments_data:

            keywords_list = data.get("keywords", [])

            fragment = Fragment(
                request_id=data["request_id"],
                keywords=keywords_list,
                start_frame=data["start_frame"],
                end_frame=data["end_frame"],
                storage_path=data["storage_path"]
            )
            self.db.add(fragment)
            fragments.append(fragment)

        self.db.flush()
        return fragments

    def get_fragments_by_request(
            self,
            request_id: int,
            user_id: Optional[int] = None
    ) -> List[Fragment]:
        stmt = select(Fragment).where(Fragment.request_id == request_id)

        if user_id:
            stmt = stmt.join(SearchRequest).where(SearchRequest.user_id == user_id)

        stmt = stmt.order_by(Fragment.start_frame)
        fragments = self.db.execute(stmt).scalars().all()

        for fragment in fragments:
            if fragment.keywords is None:
                fragment.keywords = []
            elif not isinstance(fragment.keywords, list):
                fragment.keywords = [fragment.keywords]

        return fragments

    def get_fragment(self, fragment_id: int) -> Optional[Fragment]:
        fragment = self.db.get(Fragment, fragment_id)
        if fragment and fragment.keywords is None:
            fragment.keywords = []
        return fragment

    def delete_fragments_by_request(self, request_id: int) -> int:
        stmt = select(Fragment).where(Fragment.request_id == request_id)
        fragments = self.db.execute(stmt).scalars().all()

        for fragment in fragments:
            self.db.delete(fragment)

        self.db.flush()
        return len(fragments)