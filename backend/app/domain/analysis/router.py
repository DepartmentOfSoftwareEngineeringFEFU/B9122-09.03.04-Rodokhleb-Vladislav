from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import json
import logging

from .models import AnalysisRequest, AnalysisResult, AnalysisStatus
from .video_analyzer import VideoAnalyzer
from ...shared.database import get_db
from ...shared.exceptions import NotFoundError, VideoProcessingError
from ...api.deps import get_current_user_id
from ...domain.videos.service import VideoService
from ...domain.fragments.service import FragmentService
from ...config import settings
from ...services.text_processor import TextProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

progress_storage = {}


def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    return VideoService(db=db)


def get_fragment_service(db: Session = Depends(get_db)) -> FragmentService:
    return FragmentService(db=db)


def get_video_analyzer() -> VideoAnalyzer:
    return VideoAnalyzer(verbose=settings.DEBUG)


@router.post("/start", response_model=dict)
async def start_analysis(
        request: AnalysisRequest,
        video_id: int,
        background_tasks: BackgroundTasks,
        user_id: int = Depends(get_current_user_id),
        video_service: VideoService = Depends(get_video_service),
        db: Session = Depends(get_db)
):
    try:
        logger.info("=" * 80)
        logger.info("STARTING ANALYSIS REQUEST")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Video ID: {video_id}")
        logger.info(f"Original keywords (Russian): {request.keywords}")

        video = video_service.get_video(video_id, user_id)
        if not video:
            raise NotFoundError(f"Video with id {video_id} not found")

        text_processor = TextProcessor()
        translation_map = {}

        logger.info("\nTRANSLATION PROCESS:")
        for rus_kw in request.keywords:
            eng_kw = text_processor.translate(rus_kw).strip()
            translation_map[eng_kw] = rus_kw
            logger.info(f"   '{rus_kw}' → '{eng_kw}'")

        logger.info(f"\nFINAL TRANSLATION MAP: {translation_map}")
        logger.info(f"   English keywords for detection: {list(translation_map.keys())}")

        fragment_service = FragmentService(db)
        search_request = fragment_service.create_request(
            user_id=user_id,
            video_id=video_id,
            keywords=translation_map
        )

        db.commit()
        logger.info(f"\nSearch request created: ID={search_request.id}")
        logger.info(f"   Stored in DB: {search_request.keywords}")

        background_tasks.add_task(
            _run_analysis_task,
            video_key=video.file_path,
            keywords=list(translation_map.keys()),
            request_id=search_request.id,
            db=db,
            fps=request.fps,
            confidence=request.confidence
        )

        logger.info("=" * 80)

        return {
            "request_id": search_request.id,
            "status": "processing",
            "message": "Analysis started successfully"
        }

    except NotFoundError as e:
        logger.error(f"NotFoundError: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _run_analysis_task(
        video_key: str,
        keywords: List[str],
        request_id: int,
        db: Session,
        fps: int = 5,
        confidence: float = 0.35
):
    from ...domain.fragments.service import FragmentService
    from ...domain.analysis.video_analyzer import VideoAnalyzer
    from ...shared.database import SessionLocal
    from ...domain.videos.service import VideoService

    logger.info(f"RUNNING ANALYSIS TASK")
    logger.info(f"   Request ID: {request_id}")
    logger.info(f"   Keywords for detection: {keywords}")
    logger.info(f"   FPS: {fps}, Confidence: {confidence}")

    new_db = SessionLocal()

    try:
        fragment_service = FragmentService(new_db)
        video_service = VideoService(new_db)
        analyzer = VideoAnalyzer(verbose=True)

        try:
            search_request = fragment_service.get_request(request_id)
            logger.info(f" Found search request: ID={search_request.id}")
            logger.info(f" Translation map from DB: {search_request.keywords}")
        except NotFoundError:
            logger.error(f"Request {request_id} not found in database")
            return

        video = video_service.get_video(search_request.video_id, search_request.user_id)
        logger.info(f"Video: {video.filename}, Path: {video.file_path}")

        fragment_service.update_request_status(request_id, "processing", new_db)
        new_db.commit()

        def update_progress(progress: float):
            update_progress_storage(request_id, progress)
            logger.info(f"Progress: {progress * 100:.1f}%")

        logger.info("\nStarting video analysis...")
        result = analyzer.analyze_video_from_minio(
            video_key=video_key,
            keywords=keywords,
            fps=fps,
            confidence=confidence,
            progress_callback=update_progress,
            request_id=request_id
        )

        logger.info(f"\nAnalysis result: {len(result.fragments)} fragments found")
        for i, frag in enumerate(result.fragments):
            logger.info(f"Fragment {i + 1}: keyword='{frag.keyword}', "
                        f"start={frag.start_time:.2f}s, end={frag.end_time:.2f}s")

        video_info = video_service.get_video_info(search_request.video_id, search_request.user_id)
        video_fps = video_info.fps or 30
        logger.info(f"Video FPS: {video_fps}")

        logger.info("\nSaving fragments to database...")
        saved_fragments = fragment_service.save_fragments(
            request_id=request_id,
            fragments=result.fragments,
            video_fps=video_fps,
            analysis_fps=fps,
            db=new_db
        )

        logger.info(f"Saved {len(saved_fragments)} fragments to DB")
        for f in saved_fragments:
            logger.info(f"Fragment {f.id}: keywords={f.keywords}, "
                        f"frames={f.start_frame}-{f.end_frame}")

        fragment_service.update_request_status(request_id, "completed", new_db)
        new_db.commit()

        if request_id in progress_storage:
            del progress_storage[request_id]

        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Analysis error for request {request_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            fragment_service.update_request_status(request_id, "error", new_db)
            new_db.commit()
        except:
            pass
    finally:
        new_db.close()


def update_progress_storage(request_id: int, progress: float):
    progress_storage[request_id] = progress


@router.get("/status/{request_id}", response_model=AnalysisStatus)
def get_analysis_status(
        request_id: int,
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db)
):
    fragment_service = get_fragment_service(db)

    try:
        search_request = fragment_service.repo.get_request(request_id, user_id)
        if not search_request:
            raise NotFoundError(f"Request {request_id} not found")

        progress = progress_storage.get(request_id, 0.0)

        return AnalysisStatus(
            request_id=search_request.id,
            status=search_request.status,
            progress=progress,
            error_message=None,
            created_at=search_request.created_at,
            completed_at=search_request.completed_at
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/result/{request_id}", response_model=dict)
def get_analysis_result(
        request_id: int,
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db)
):
    fragment_service = get_fragment_service(db)

    try:
        search_request = fragment_service.get_request(request_id, user_id, db)
        fragments = fragment_service.get_fragments_by_request(request_id, user_id, db)

        if fragments:
            sample = fragments[0]

            all_keywords = set()
            for f in fragments:
                if isinstance(f.keywords, list):
                    all_keywords.update(f.keywords)
                elif isinstance(f.keywords, str):
                    try:
                        parsed = json.loads(f.keywords)
                        if isinstance(parsed, list):
                            all_keywords.update(parsed)
                        else:
                            all_keywords.add(str(parsed))
                    except:
                        all_keywords.add(f.keywords)
            logger.info(f"All unique keywords in fragments: {all_keywords}")
        else:
            logger.warning("NO fragments found in database!")

        fragments_by_keyword = {}
        for frag in fragments:
            keywords_list = frag.keywords if isinstance(frag.keywords, list) else []
            if isinstance(frag.keywords, str):
                try:
                    keywords_list = json.loads(frag.keywords)
                    if not isinstance(keywords_list, list):
                        keywords_list = [keywords_list]
                except:
                    keywords_list = [frag.keywords]

            for kw in keywords_list:
                if kw not in fragments_by_keyword:
                    fragments_by_keyword[kw] = []
                fragments_by_keyword[kw].append({
                    "id": frag.id,
                    "start_frame": frag.start_frame,
                    "end_frame": frag.end_frame,
                    "storage_path": frag.storage_path,
                    "created_at": frag.created_at.isoformat() if frag.created_at else None
                })

        if isinstance(search_request.keywords, dict):
            requested_keys = set(search_request.keywords.keys())
            fragment_keys = set(fragments_by_keyword.keys())

            if requested_keys != fragment_keys:
                missing = requested_keys - fragment_keys
                extra = fragment_keys - requested_keys
                if missing:
                    logger.warning(f"Missing keywords in fragments: {missing}")
                if extra:
                    logger.warning(f"Extra keywords in fragments: {extra}")

        return {
            "request_id": search_request.id,
            "video_id": search_request.video_id,
            "keywords": search_request.keywords,
            "status": search_request.status,
            "created_at": search_request.created_at.isoformat() if search_request.created_at else None,
            "completed_at": search_request.completed_at.isoformat() if search_request.completed_at else None,
            "fps": 2,
            "total_fragments": len(fragments),
            "fragments_by_keyword": fragments_by_keyword
        }
    except NotFoundError as e:
        logger.error(f"NotFoundError: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/result/{request_id}/fragments")
def get_fragment_urls(
        request_id: int,
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
        expires_in: int = 3600
):

    fragment_service = get_fragment_service(db)

    try:
        search_request = fragment_service.get_request(request_id, user_id, db)

        translation_map = search_request.keywords
        if isinstance(translation_map, str):
            try:
                translation_map = json.loads(translation_map)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse translation_map: {e}")
                translation_map = {}

        fragments = fragment_service.get_fragments_by_request(request_id, user_id, db)
        if fragments:
            sample = fragments[0]
            if isinstance(sample.keywords, str):
                logger.info(f"Keywords as string: {sample.keywords[:100]}...")

        fragment_urls = []
        for frag in fragments:
            try:
                url = fragment_service.get_fragment_url(frag.id, expires_in)

                keywords_en = []
                if isinstance(frag.keywords, list):
                    keywords_en = frag.keywords
                elif isinstance(frag.keywords, str):
                    try:
                        parsed = json.loads(frag.keywords)
                        if isinstance(parsed, list):
                            keywords_en = parsed
                        else:
                            keywords_en = [str(parsed)]
                    except:
                        keywords_en = [frag.keywords]
                else:
                    keywords_en = [str(frag.keywords)]

                fragment_urls.append({
                    "id": frag.id,
                    "keywords_en": keywords_en,
                    "start_frame": frag.start_frame,
                    "end_frame": frag.end_frame,
                    "url": url
                })
            except Exception as e:
                logger.error(f"Failed to get URL for fragment {frag.id}: {e}")

        original_keywords = list(translation_map.values()) if isinstance(translation_map, dict) else []

        return {
            "request_id": request_id,
            "fragments": fragment_urls,
            "translation_map": translation_map,
            "original_keywords": original_keywords,
            "expires_in": expires_in
        }
    except NotFoundError as e:
        logger.error(f"NotFoundError: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))