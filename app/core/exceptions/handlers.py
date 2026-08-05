import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.base import AppException
from app.core.responses import error_response

logger = logging.getLogger(__name__)


def _log_server_exception(
    request: Request,
    exc: Exception,
    *,
    status_code: int,
    error_code: str,
) -> None:
    logger.error(
        (
            "Server request failed method=%s path=%s status_code=%s "
            "error_code=%s error_type=%s"
        ),
        request.method,
        request.url.path,
        status_code,
        error_code,
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        if exc.status_code >= 500:
            _log_server_exception(
                request,
                exc,
                status_code=exc.status_code,
                error_code=exc.code,
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                code=exc.code,
                message=exc.message,
                data=None,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_response(
                code="VALIDATION_ERROR",
                message="요청 값이 올바르지 않습니다.",
                data={
                    "errors": jsonable_encoder(exc.errors()),
                },
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "HTTP 요청 처리 중 오류가 발생했습니다."
        )

        if exc.status_code >= 500:
            _log_server_exception(
                request,
                exc,
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
            )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                code="HTTP_ERROR",
                message=message,
                data=None,
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        _log_server_exception(
            request,
            exc,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )

        return JSONResponse(
            status_code=500,
            content=error_response(
                code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                data=None,
            ),
        )
