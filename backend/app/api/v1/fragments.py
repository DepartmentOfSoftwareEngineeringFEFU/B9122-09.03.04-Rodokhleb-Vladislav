from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...domain.fragments.router import router as fragments_domain_router
from ...shared.database import get_db

router = APIRouter()
router.include_router(fragments_domain_router)