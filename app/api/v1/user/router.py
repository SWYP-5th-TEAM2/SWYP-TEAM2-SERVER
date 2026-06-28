from fastapi import APIRouter

from app.api.v1.user.fcm_token import router as fcm_token_router
from app.api.v1.user.profile import router as profile_router

user_router = APIRouter(
    prefix="/users",
    tags=["User"],
)

user_router.include_router(fcm_token_router)
user_router.include_router(profile_router)
