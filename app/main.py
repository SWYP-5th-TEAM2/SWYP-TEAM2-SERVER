from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.base.router import router as base_router
from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions.handlers import register_exception_handlers
from app.core.redis import connect_redis, close_redis
from app.services.plan.auto_close_service import start_plan_auto_close_worker, stop_plan_auto_close_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_redis()
    plan_auto_close_task = start_plan_auto_close_worker()
    try:
        yield
    finally:
        await stop_plan_auto_close_worker(plan_auto_close_task)
        await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(
        base_router,
        prefix="/api",
    )

    app.include_router(
        v1_router,
        prefix="/api/v1",
    )

    return app


app = create_app()