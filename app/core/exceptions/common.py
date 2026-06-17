from http import HTTPStatus

from app.core.exceptions.base import AppException


class BadRequestException(AppException):
    def __init__(
        self,
        code: str = "BAD_REQUEST",
        message: str = "잘못된 요청입니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
        )


class UnauthorizedException(AppException):
    def __init__(
        self,
        code: str = "UNAUTHORIZED",
        message: str = "인증이 필요합니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    def __init__(
        self,
        code: str = "FORBIDDEN",
        message: str = "접근 권한이 없습니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
        )


class NotFoundException(AppException):
    def __init__(
        self,
        code: str = "RESOURCE_NOT_FOUND",
        message: str = "요청한 리소스를 찾을 수 없습니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
        )


class ConflictException(AppException):
    def __init__(
        self,
        code: str = "CONFLICT",
        message: str = "이미 존재하는 리소스입니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.CONFLICT,
        )