from fastapi import APIRouter

from app.api.v1.places.search import router as search_router
from app.api.v1.places.crud import router as crud_router

places_router = APIRouter(
    prefix="/places",
    tags=["Place"],
)

# /search가 /{place_id}보다 먼저 등록되어야 경로 충돌을 피할 수 있습니다.
places_router.include_router(search_router)
places_router.include_router(crud_router)
