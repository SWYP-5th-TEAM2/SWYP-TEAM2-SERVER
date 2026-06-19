from fastapi import APIRouter

from app.api.v1.auth.session import router as session_router

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

auth_router.include_router(session_router)