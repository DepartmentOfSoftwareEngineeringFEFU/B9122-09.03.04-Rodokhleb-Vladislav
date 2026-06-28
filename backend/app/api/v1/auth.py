from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...domain.auth.router import router as auth_domain_router
from ...shared.database import get_db


router = APIRouter()
router.include_router(auth_domain_router)