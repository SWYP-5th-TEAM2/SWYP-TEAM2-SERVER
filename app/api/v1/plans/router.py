from fastapi import APIRouter

from app.api.v1.plans.plans import router as plans_api_router

plans_router = APIRouter(
    prefix="/plans",
    tags=["Plan"],
)

plans_router.include_router(plans_api_router)
