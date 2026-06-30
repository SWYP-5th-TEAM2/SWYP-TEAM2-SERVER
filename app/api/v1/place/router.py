from fastapi import APIRouter

from app.api.v1.place.search import router as search_router

place_router = APIRouter(
    prefix="/place",
    tags=["Place"],
)

place_router.include_router(search_router)
