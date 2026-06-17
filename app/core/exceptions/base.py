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