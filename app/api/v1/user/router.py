from fastapi import APIRouter

from app.api.v1.user.fcm_token import router as fcm_token_router
from app.api.v1.user.profile import router as profile_router
from app.api.v1.user.recurring_schedule import router as recurring_schedule_router
from app.api.v1.user.notification_settings import router as notification_settings_router
from app.api.v1.user.withdrawal import router as withdrawal_router
from app.api.v1.user.terms import router as terms_router

user_router = APIRouter(
    prefix="/users",
    tags=["User"],
)

user_router.include_router(fcm_token_router)
user_router.include_router(profile_router)
user_router.include_router(recurring_schedule_router)
user_router.include_router(notification_settings_router)
user_router.include_router(withdrawal_router)
user_router.include_router(terms_router)
