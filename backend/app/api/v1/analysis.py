from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...domain.analysis.router import router as analysis_domain_router
from ...shared.database import get_db

router = APIRouter()
router.include_router(analysis_domain_router)