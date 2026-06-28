from app.core.exceptions.common import BadRequestException, NotFoundException


class FcmTokenMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="FCM_TOKEN_MISSING",
            message="FCM 토큰 입력은 필수입니다.",
        )


class FcmTokenBlankException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="FCM_TOKEN_BLANK",
            message="FCM 토큰은 비어있을 수 없습니다.",
        )


class DeviceTypeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="DEVICE_TYPE_MISSING",
            message="기기 타입 입력은 필수입니다.",
        )


class UnsupportedDeviceTypeException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_DEVICE_TYPE",
            message="지원하지 않는 기기 유형입니다.",
        )


class UserNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
        )
