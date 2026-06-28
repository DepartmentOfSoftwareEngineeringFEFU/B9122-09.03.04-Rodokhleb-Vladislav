from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...domain.users.router import router as users_domain_router
from ...shared.database import get_db

router = APIRouter()
router.include_router(users_domain_router)