from app.core.exceptions.common import (
    BadRequestException,
    InternalServerException,
    NotFoundException,
)


class RecurringScheduleIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_RECURRING_SCHEDULE_ID",
            message="ID 형식이 올바르지 않습니다.",
        )


class RecurringScheduleRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_REQUEST_BODY_MISSING",
            message="요청 본문이 필요합니다.",
        )


class RecurringScheduleUpdateFieldsMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_UPDATE_FIELDS_MISSING",
            message="수정할 반복 일정 정보를 입력해주세요.",
        )


class RecurringScheduleTitleMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_TITLE_MISSING",
            message="반복 일정 제목을 입력해주세요.",
        )


class RecurringScheduleTitleTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_TITLE_TOO_LONG",
            message="반복 일정 제목은 최대 12자까지 입력할 수 있습니다.",
        )


class RecurringScheduleDaysMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_DAYS_MISSING",
            message="반복 요일을 선택해주세요.",
        )


class RecurringScheduleDayInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_RECURRING_SCHEDULE_DAY",
            message="요일 값이 올바르지 않습니다.",
        )


class RecurringScheduleDaysDuplicatedException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="DUPLICATED_RECURRING_SCHEDULE_DAY",
            message="반복 요일은 중복될 수 없습니다.",
        )


class RecurringScheduleStartTimeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_START_TIME_MISSING",
            message="시작 시간을 입력해주세요.",
        )


class RecurringScheduleEndTimeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_END_TIME_MISSING",
            message="종료 시간을 입력해주세요.",
        )


class RecurringScheduleTimeInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_RECURRING_SCHEDULE_TIME",
            message="시간 형식이 올바르지 않습니다.",
        )


class RecurringScheduleTimeRangeInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_RECURRING_SCHEDULE_TIME_RANGE",
            message="시작 시간은 종료 시간보다 빨라야 합니다.",
        )


class RecurringScheduleUserNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_USER_NOT_FOUND",
            message="사용자 정보를 찾을 수 없습니다.",
        )


class RecurringScheduleNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_NOT_FOUND",
            message="반복 일정을 찾을 수 없습니다.",
        )


class RecurringScheduleListFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_LIST_FAILED",
            message="반복 일정 조회 중 오류가 발생했습니다.",
        )


class RecurringScheduleCreateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_CREATE_FAILED",
            message="반복 일정 등록 중 오류가 발생했습니다.",
        )


class RecurringScheduleUpdateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_UPDATE_FAILED",
            message="반복 일정 수정 중 오류가 발생했습니다.",
        )


class RecurringScheduleDeleteFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="RECURRING_SCHEDULE_DELETE_FAILED",
            message="반복 일정 삭제 중 오류가 발생했습니다.",
        )
