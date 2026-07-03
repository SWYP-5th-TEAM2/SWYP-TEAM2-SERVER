from fastapi import APIRouter

from app.api.v1.auth.router import auth_router
from app.api.v1.room.router import room_router
from app.api.v1.common.router import common_router
from app.api.v1.user.router import user_router
from app.api.v1.place.router import place_router
from app.api.v1.places.router import places_router
from app.api.v1.plans.router import plans_router
from app.api.v1.notifications.router import notifications_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(room_router)
router.include_router(common_router)
router.include_router(place_router)
router.include_router(places_router)

router.include_router(plans_router)
router.include_router(notifications_router)
