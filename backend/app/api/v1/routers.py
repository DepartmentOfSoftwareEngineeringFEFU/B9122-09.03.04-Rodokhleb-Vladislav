from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .videos import router as videos_router
from .analysis import router as analysis_router
from .fragments import router as fragments_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(videos_router)
router.include_router(analysis_router)
router.include_router(fragments_router)