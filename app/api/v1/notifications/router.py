from fastapi import APIRouter

from app.api.v1.notifications.notifications import router as notifications_api_router

notifications_router = APIRouter(
    prefix="/notifications",
    tags=["Notice"],
)

notifications_router.include_router(notifications_api_router)
