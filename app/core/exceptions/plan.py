from app.core.exceptions.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
)


class PlanRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_REQUEST_BODY_MISSING", message="요청 본문이 필요합니다.")


class PlanRoomIdMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_ROOM_ID_MISSING", message="방 ID를 입력해주세요.")


class PlanRoomIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_ROOM_ID", message="올바르지 않은 방 ID입니다.")


class PlanPlaceIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_PLACE_ID", message="올바르지 않은 장소 후보 ID입니다.")


class PlanIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_ID", message="올바르지 않은 약속 제안 ID입니다.")


class PlanScheduledAtMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_SCHEDULED_AT_MISSING", message="약속 일시를 입력해주세요.")


class PlanScheduledAtInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_SCHEDULED_AT", message="약속 일시 형식이 올바르지 않습니다.")


class PlanResponseDeadlineMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_DEADLINE_MISSING", message="응답 마감 시각을 입력해주세요.")


class PlanResponseDeadlineInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_RESPONSE_DEADLINE", message="응답 마감 시각 형식이 올바르지 않습니다.")


class PlanScheduledAtPastException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_SCHEDULED_AT_PAST", message="약속 일시는 현재 시각 이후로 설정해주세요.")


class PlanResponseDeadlinePastException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_DEADLINE_PAST", message="응답 마감 시각은 현재 시각 이후로 설정해주세요.")


class PlanResponseDeadlineAfterScheduleException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_DEADLINE_AFTER_SCHEDULE", message="응답 마감 시각은 약속 일시보다 이전이어야 합니다.")


class PlanStatusFilterInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_STATUS_FILTER", message="지원하지 않는 약속 상태 필터입니다.")


class PlanPageValueInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_PAGE_VALUE", message="페이지 요청 값이 올바르지 않습니다.")


class PlanResponseStatusMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_STATUS_MISSING", message="응답 상태를 선택해주세요.")


class PlanTargetUserIdMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_TARGET_USER_ID_MISSING", message="알림을 보낼 사용자 ID를 입력해주세요.")


class PlanTargetUserIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="INVALID_PLAN_TARGET_USER_ID", message="올바르지 않은 사용자 ID입니다.")


class UnsupportedPlanResponseStatusException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(code="UNSUPPORTED_PLAN_RESPONSE_STATUS", message="지원하지 않는 응답 상태입니다.")


class PlanRoomAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_ROOM_ACCESS_DENIED", message="해당 약속 제안에 접근할 권한이 없습니다.")


class PlanCloseAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_CLOSE_ACCESS_DENIED", message="해당 약속 제안을 마감할 권한이 없습니다.")


class PlanResponseAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_ACCESS_DENIED", message="해당 약속 제안의 응답 대상이 아닙니다.")


class PlanRoomNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_ROOM_NOT_FOUND", message="존재하지 않는 방입니다.")


class PlanPlaceNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_PLACE_NOT_FOUND", message="존재하지 않는 장소 후보입니다.")


class PlanNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_NOT_FOUND", message="존재하지 않는 약속 제안입니다.")


class PlanDeletedException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_DELETED", message="삭제된 약속 제안입니다.")


class PlanPlaceNotInRoomException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_PLACE_NOT_IN_ROOM", message="해당 방의 장소 후보가 아닙니다.")


class PlanTargetMemberMissingException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_TARGET_MEMBER_MISSING", message="응답을 요청할 멤버가 없습니다.")


class PlanAlreadyExistsException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_ALREADY_EXISTS", message="이미 진행 중인 약속 제안이 있습니다.")


class PlanNoDrawablePlaceException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_NO_DRAWABLE_PLACE", message="뽑기 가능한 장소 후보가 없습니다.")


class PlanAlreadyClosedException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_ALREADY_CLOSED", message="이미 마감된 약속 제안입니다.")


class PlanResponseDeadlinePassedException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_DEADLINE_PASSED", message="응답 마감 시간이 지났습니다.")


class PlanPendingMemberNotFoundException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_PENDING_MEMBER_NOT_FOUND", message="알림을 보낼 미응답 멤버가 없습니다.")




class PlanTicketNotConfirmedException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_TICKET_NOT_CONFIRMED", message="확정되지 않은 약속 제안은 티켓을 조회할 수 없습니다.")


class PlanNoAttendingMemberException(ConflictException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_NO_ATTENDING_MEMBER", message="참석 가능한 멤버가 없어 약속을 확정할 수 없습니다.")


class PlanDrawFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_DRAW_FAILED", message="장소 후보 뽑기 중 오류가 발생했습니다.")


class PlanCreateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_CREATE_FAILED", message="약속 제안 생성 중 오류가 발생했습니다.")


class PlanResponsesLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSES_LOOKUP_FAILED", message="응답 현황 조회 중 오류가 발생했습니다.")


class PlanReminderFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_REMINDER_FAILED", message="미응답자 알림 발송 중 오류가 발생했습니다.")


class PlanCloseFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_CLOSE_FAILED", message="응답 마감 중 오류가 발생했습니다.")


class PlanListLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_LIST_LOOKUP_FAILED", message="약속 목록 조회 중 오류가 발생했습니다.")


class PlanResponseSaveFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_RESPONSE_SAVE_FAILED", message="응답 저장 중 오류가 발생했습니다.")


class PlanInvitationLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_INVITATION_LOOKUP_FAILED", message="같이 갈래? 응답 화면 조회 중 오류가 발생했습니다.")


class PlanTicketLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(code="PLAN_TICKET_LOOKUP_FAILED", message="약속 티켓 조회 중 오류가 발생했습니다.")
