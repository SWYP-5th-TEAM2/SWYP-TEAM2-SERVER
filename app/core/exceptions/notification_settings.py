from app.core.exceptions.common import BadRequestException, InternalServerException


class NotificationSettingsRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_SETTINGS_REQUEST_BODY_MISSING",
            message="요청 본문이 필요합니다.",
        )


class UnsupportedNotificationSettingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_NOTIFICATION_SETTING",
            message="지원하지 않는 설정 항목입니다.",
        )


class NotificationSettingsUpdateFieldsMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_SETTINGS_UPDATE_FIELDS_MISSING",
            message="수정할 알림 설정을 입력해주세요.",
        )


class NotificationSettingValueInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_NOTIFICATION_SETTING_VALUE",
            message="알림 설정 값은 true 또는 false여야 합니다.",
        )


class NotificationSettingsFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_SETTINGS_FAILED",
            message="알림 설정 중 오류가 발생했습니다.",
        )
