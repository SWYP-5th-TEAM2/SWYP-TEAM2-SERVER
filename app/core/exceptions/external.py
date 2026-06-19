from app.core.exceptions import ServiceUnavailableException


class RedisUnavailableException(ServiceUnavailableException):
    def __init__(self) -> None:
        super().__init__(
            code="REDIS_UNAVAILABLE",
            message="Redis 서버에 연결할 수 없습니다.",
        )