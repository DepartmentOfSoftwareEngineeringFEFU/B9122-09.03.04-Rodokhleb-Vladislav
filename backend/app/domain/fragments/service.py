from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .repository import FragmentRepository
from .models import (
    FragmentResponse, FragmentCreate,
    SearchRequestResponse, SearchRequestStatus,
    SearchRequestCreate
)
from ...shared.exceptions import NotFoundError, ValidationError
from ...shared.minio_client import minio_client
from ...config import settings
from ...domain.analysis.models import Fragment as AnalysisFragment
import logging
logger = logging.getLogger(__name__)


class FragmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FragmentRepository(db)

    def create_request(
            self,
            user_id: int,
            video_id: int,
            keywords: dict,
            db: Optional[Session] = None
    ) -> SearchRequestResponse:
        repo = FragmentRepository(db or self.db)

        search_request = repo.create_request(
            user_id=user_id,
            video_id=video_id,
            keywords=keywords
        )

        if db is None:
            self.db.commit()

        return SearchRequestResponse.model_validate(search_request)

    def get_request(
            self,
            request_id: int,
            user_id: Optional[int] = None,
            db: Optional[Session] = None
    ) -> SearchRequestResponse:
        repo = FragmentRepository(db or self.db)

        search_request = repo.get_request(request_id, user_id)
        if not search_request:
            raise NotFoundError(f"Search request {request_id} not found")

        return SearchRequestResponse.model_validate(search_request)

    def get_user_requests(
            self,
            user_id: int,
            page: int = 1,
            size: int = 50,
            db: Optional[Session] = None
    ) -> Dict[str, Any]:
        repo = FragmentRepository(db or self.db)

        skip = (page - 1) * size
        requests, total = repo.get_requests_by_user(user_id, skip=skip, limit=size)

        return {
            "items": [SearchRequestResponse.model_validate(r) for r in requests],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

    def update_request_status(
            self,
            request_id: int,
            status: str,
            db: Optional[Session] = None
    ) -> SearchRequestResponse:
        repo = FragmentRepository(db or self.db)

        search_request = repo.update_request_status(
            request_id=request_id,
            status=status
        )

        if db is None:
            self.db.commit()

        return SearchRequestResponse.model_validate(search_request)

    def get_request_status(
            self,
            request_id: int,
            user_id: int,
            db: Optional[Session] = None
    ) -> SearchRequestStatus:
        repo = FragmentRepository(db or self.db)

        search_request = repo.get_request(request_id, user_id)
        if not search_request:
            raise NotFoundError(f"Search request {request_id} not found")

        return SearchRequestStatus(
            request_id=search_request.id,
            status=search_request.status,
            created_at=search_request.created_at,
            completed_at=search_request.completed_at
        )

    def delete_request(self, request_id: int, user_id: int) -> bool:
        search_request = self.repo.get_request(request_id, user_id)
        if not search_request:
            raise NotFoundError(f"Search request {request_id} not found")

        fragments = self.repo.get_fragments_by_request(request_id, user_id)
        for fragment in fragments:
            if fragment.storage_path:
                parts = fragment.storage_path.split('/', 1)
                if len(parts) == 2:
                    folder = parts[0]
                    object_name = parts[1]
                    minio_client.delete_file(object_name, folder)

        self.repo.delete_fragments_by_request(request_id)

        result = self.repo.delete_request(request_id)
        self.db.commit()

        return result


    def save_fragments(
            self,
            request_id: int,
            fragments: List[AnalysisFragment],
            video_fps: float,
            analysis_fps: int = 2,
            db: Optional[Session] = None
    ) -> List[FragmentResponse]:

        repo = FragmentRepository(db or self.db)

        frame_step = video_fps / analysis_fps
        logger.info(f"   Video FPS: {video_fps}, Analysis FPS: {analysis_fps}")
        logger.info(f"   Frame step: {frame_step}")

        fragments_data = []
        for idx, frag in enumerate(fragments):
            start_frame_analysis = int(round(frag.start_time * analysis_fps))
            end_frame_analysis = int(round(frag.end_time * analysis_fps))

            start_frame_original = int(round(start_frame_analysis * frame_step))
            end_frame_original = int(round(end_frame_analysis * frame_step))

            storage_path = f"{settings.MINIO_FOLDER_FRAGMENTS}/request_{request_id}/fragment_{idx + 1}_{frag.keyword.replace(' ', '_')}.mp4"


            fragments_data.append({
                "request_id": request_id,
                "keywords": [frag.keyword],
                "start_frame": start_frame_original,
                "end_frame": end_frame_original,
                "storage_path": storage_path
            })

        saved_fragments = repo.create_fragments_batch(fragments_data)

        if db is None:
            self.db.commit()


        result = []
        for f in saved_fragments:
            keywords = f.keywords
            if isinstance(keywords, str):
                import json
                keywords = json.loads(keywords)

            result.append(FragmentResponse(
                id=f.id,
                request_id=f.request_id,
                keywords=keywords,
                start_frame=f.start_frame,
                end_frame=f.end_frame,
                storage_path=f.storage_path,
                created_at=f.created_at
            ))

        return result

    def get_fragments_by_request(
            self,
            request_id: int,
            user_id: int,
            db: Optional[Session] = None
    ) -> List[FragmentResponse]:
        repo = FragmentRepository(db or self.db)

        fragments = repo.get_fragments_by_request(request_id, user_id)

        result = []
        for frag in fragments:
            keywords = frag.keywords if isinstance(frag.keywords, list) else []

            result.append(FragmentResponse(
                id=frag.id,
                request_id=frag.request_id,
                keywords=keywords,
                start_frame=frag.start_frame,
                end_frame=frag.end_frame,
                storage_path=frag.storage_path,
                created_at=frag.created_at
            ))

        return result

    def get_fragment(self, fragment_id: int) -> FragmentResponse:
        fragment = self.repo.get_fragment(fragment_id)
        if not fragment:
            raise NotFoundError(f"Fragment {fragment_id} not found")

        keywords = fragment.keywords if isinstance(fragment.keywords, list) else []

        return FragmentResponse(
            id=fragment.id,
            request_id=fragment.request_id,
            keywords=keywords,
            start_frame=fragment.start_frame,
            end_frame=fragment.end_frame,
            storage_path=fragment.storage_path,
            created_at=fragment.created_at
        )

    def get_fragment_url(self, fragment_id: int, expires_in: int = 3600) -> str:
        fragment = self.repo.get_fragment(fragment_id)
        if not fragment:
            raise NotFoundError(f"Fragment {fragment_id} not found")

        parts = fragment.storage_path.split('/', 1)
        if len(parts) == 2:
            folder = parts[0]
            object_name = parts[1]
        else:
            folder = settings.MINIO_FOLDER_FRAGMENTS
            object_name = fragment.storage_path

        try:
            url = minio_client.get_file_url(
                object_name=object_name,
                folder=folder,
                expires_in=expires_in
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to get fragment URL: {e}")