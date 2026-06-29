from app.core.exceptions.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
)


class RoomRequestBodyMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_REQUEST_BODY_MISSING",
            message="요청 본문이 필요합니다.",
        )


class RoomNameMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_NAME_MISSING",
            message="방 이름을 입력해주세요.",
        )


class RoomNameTooLongException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_NAME_TOO_LONG",
            message="방 이름은 최대 12자까지 입력할 수 있습니다.",
        )


class RoomNameInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_ROOM_NAME",
            message="방 이름 형식이 올바르지 않습니다.",
        )


class RoomColorMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_COLOR_MISSING",
            message="방 색상을 입력해주세요.",
        )


class RoomColorInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_ROOM_COLOR",
            message="방 색상 형식이 올바르지 않습니다.",
        )


class RoomIdInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_ROOM_ID",
            message="방 ID 형식이 올바르지 않습니다.",
        )


class InviteCodeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVITE_CODE_MISSING",
            message="초대코드를 입력해주세요.",
        )


class InviteCodeInvalidException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_INVITE_CODE",
            message="초대코드 형식이 올바르지 않습니다.",
        )


class WithdrawnRoomUserException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="WITHDRAWN_ROOM_USER",
            message="탈퇴한 회원입니다.",
        )


class BlockedRoomUserException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="BLOCKED_ROOM_USER",
            message="차단된 사용자입니다.",
        )


class RoomAccessDeniedException(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_ACCESS_DENIED",
            message="해당 방에 대한 접근 권한이 없습니다.",
        )


class RoomNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_NOT_FOUND",
            message="방을 찾을 수 없습니다.",
        )


class InviteCodeRoomNotFoundException(NotFoundException):
    def __init__(self) -> None:
        super().__init__(
            code="INVITE_CODE_ROOM_NOT_FOUND",
            message="유효하지 않은 초대코드입니다.",
        )


class RoomAlreadyJoinedException(ConflictException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_ALREADY_JOINED",
            message="이미 가입된 방입니다.",
        )


class RoomCreateFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_CREATE_FAILED",
            message="방 생성 중 오류가 발생했습니다.",
        )


class InviteCodeLookupFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="INVITE_CODE_LOOKUP_FAILED",
            message="초대코드 조회 중 오류가 발생했습니다.",
        )


class RoomJoinFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="ROOM_JOIN_FAILED",
            message="방 가입 중 오류가 발생했습니다.",
        )
