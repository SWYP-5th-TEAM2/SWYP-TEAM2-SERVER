from fastapi import APIRouter

from app.api.v1.auth.router import auth_router
from app.api.v1.common.router import common_router
from app.api.v1.user.router import user_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(common_router)