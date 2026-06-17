from http import HTTPStatus


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = int(status_code)
        super().__init__(message)


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


class UserNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_NOT_FOUND",
            message="가입되지 않은 사용자입니다.",
        )
