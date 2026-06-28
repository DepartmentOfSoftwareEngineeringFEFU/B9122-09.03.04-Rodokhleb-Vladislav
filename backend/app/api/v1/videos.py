from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...domain.videos.router import router as videos_domain_router
from ...shared.database import get_db

router = APIRouter()
router.include_router(videos_domain_router)