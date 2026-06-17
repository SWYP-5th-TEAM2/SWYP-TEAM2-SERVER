from fastapi import FastAPI

from app.api.router.health import router as health_router
from app.config import settings
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    register_exception_handlers(app)

    app.include_router(
        health_router,
        prefix="/api/v1",
    )

    return app


app = create_app()
