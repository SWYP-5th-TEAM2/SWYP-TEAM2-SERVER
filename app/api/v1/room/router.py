from fastapi import APIRouter

from app.api.v1.room.room_info import router as room_info_router


room_router = APIRouter(
    prefix="/rooms",
    tags=["Room"],
)

room_router.include_router(room_info_router)