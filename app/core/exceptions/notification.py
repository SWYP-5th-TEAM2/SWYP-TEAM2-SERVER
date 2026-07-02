from app.core.exceptions.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
)


class NotificationIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_NOTIFICATION_ID", message="올바르지 않은 알림 ID입니다.")


class NotificationPageValueInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_NOTIFICATION_PAGE_VALUE", message="페이지 요청 값이 올바르지 않습니다.")


class NotificationAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_ACCESS_DENIED", message="해당 알림에 접근할 권한이 없습니다.")


class NotificationResponseAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_RESPONSE_ACCESS_DENIED", message="해당 약속 제안에 응답할 권한이 없습니다.")


class NotificationNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_NOT_FOUND", message="존재하지 않는 알림입니다.")


class NotificationDeletedException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_DELETED", message="삭제된 알림입니다.")


class NotificationPlanNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_PLAN_NOT_FOUND", message="존재하지 않는 약속 제안입니다.")


class NotificationNotPlanResponseException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_NOT_PLAN_RESPONSE", message="해당 알림은 약속 응답 화면으로 이동할 수 없습니다.")


class NotificationPlanAlreadyClosedException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_PLAN_ALREADY_CLOSED", message="이미 마감된 약속 제안입니다.")


class NotificationPlanCanceledException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_PLAN_CANCELED", message="취소된 약속 제안입니다.")


class NotificationListLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_LIST_LOOKUP_FAILED", message="알림 목록 조회 중 오류가 발생했습니다.")


class NotificationVoteScreenLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_VOTE_SCREEN_LOOKUP_FAILED", message="약속 응답 화면 조회 중 오류가 발생했습니다.")


class NotificationReadFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_READ_FAILED", message="알림 읽음 처리 중 오류가 발생했습니다.")


class NotificationReadAllFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="NOTIFICATION_READ_ALL_FAILED", message="알림 전체 읽음 처리 중 오류가 발생했습니다.")
