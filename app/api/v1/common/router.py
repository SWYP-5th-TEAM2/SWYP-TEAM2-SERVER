from fastapi import APIRouter

from app.api.v1.common.image import router as image_router
from app.api.v1.common.terms import router as terms_router

common_router = APIRouter(
    prefix="/common",
    tags=["Common"],
)

common_router.include_router(image_router)
common_router.include_router(terms_router)
