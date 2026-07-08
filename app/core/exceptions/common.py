from http import HTTPStatus

from app.core.exceptions.base import AppException

# 400 BAD REQUEST
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


# 401 UNAUTHORIZED
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


# 403 FORBIDDEN
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


# 404 NOT FOUND
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


# 409 CONFLICT
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


# 500 INTERNAL SERVER ERROR
class InternalServerException(AppException):
    def __init__(
        self,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "서버 내부 오류가 발생했습니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class TermsNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="TERMS_NOT_FOUND",
            message="약관을 찾을 수 없습니다.",
        )


class TermsLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="TERMS_LOOKUP_FAILED",
            message="서버 내부 오류가 발생했습니다.",
        )


# 502 BAD GATEWAY
class BadGatewayException(AppException):
    def __init__(
        self,
        code: str = "BAD_GATEWAY",
        message: str = "외부 서비스 처리 중 오류가 발생했습니다.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY
        )

# 503 SERVICE UNAVAILABLE
class ServiceUnavailableException(AppException):
    def __init__(
        self,
        code: str = "SERVICE_UNAVAILABLE",
        message: str = "일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
