import re
import secrets
import string
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BlockedRoomUserException,
    ForbiddenException,
    InviteCodeInvalidException,
    InviteCodeLookupFailedException,
    InviteCodeMissingException,
    InviteCodeRoomNotFoundException,
    RoomAccessDeniedException,
    RoomAlreadyJoinedException,
    RoomColorInvalidException,
    RoomColorMissingException,
    RoomCreateFailedException,
    RoomIdInvalidException,
    RoomJoinFailedException,
    RoomNameInvalidException,
    RoomNameMissingException,
    RoomNameTooLongException,
    RoomNotFoundException,
    RoomRequestBodyMissingException,
    UserNotFoundException,
    WithdrawnRoomUserException,
)
from app.models import User
from app.models.user.enums import UserAccountStatus
from app.repository.room import (
    create_room_member,
    create_room_with_host,
    find_active_room_member,
    find_room_by_id,
    find_room_by_invite_code,
)
from app.repository.user import find_user_by_id
from app.schemas.room import (
    CreateRoomRequest,
    CreateRoomResponse,
    InviteCodeResponse,
    JoinRoomRequest,
    JoinRoomResponse,
)

MAX_ROOM_NAME_LENGTH = 12
INVITE_CODE_LENGTH = 6
INVITE_CODE_ALPHABET = string.ascii_uppercase + string.digits
INVITE_CODE_GENERATION_ATTEMPTS = 10

ROOM_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
INVITE_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6}$")


def _get_constraint_name(exc: IntegrityError) -> str | None:
    diagnostic = getattr(exc.orig, "diag", None)
    return getattr(diagnostic, "constraint_name", None)

# 활성 유저 검증
def _ensure_active_user(
    db: Session,
    *,
    user_id: UUID,
    use_detailed_status_error: bool = False,
) -> User:
    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )
    if user is None:
        raise UserNotFoundException()

    if use_detailed_status_error:
        if user.status == UserAccountStatus.WITHDRAWN:
            raise WithdrawnRoomUserException()
        if user.status == UserAccountStatus.BLOCKED:
            raise BlockedRoomUserException()

    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    return user

# 방 이름 검증
def _validate_room_name(room_name: object) -> str:
    if room_name is None:
        raise RoomNameMissingException()
    if not isinstance(room_name, str) or not room_name.strip():
        raise RoomNameInvalidException()

    normalized_room_name = room_name.strip()
    if len(normalized_room_name) > MAX_ROOM_NAME_LENGTH:
        raise RoomNameTooLongException()

    return normalized_room_name

# 색상코드 검증
def _validate_room_color(room_color: object) -> str:
    if room_color is None:
        raise RoomColorMissingException()
    if (
        not isinstance(room_color, str)
        or ROOM_COLOR_PATTERN.fullmatch(room_color) is None
    ):
        raise RoomColorInvalidException()

    return room_color.upper()


def _parse_room_id(room_id: str) -> UUID:
    try:
        return UUID(room_id)
    except (TypeError, ValueError):
        raise RoomIdInvalidException()

# 초대 코드 검증
def _validate_invite_code(invite_code: object) -> str:
    if invite_code is None:
        raise InviteCodeMissingException()
    if not isinstance(invite_code, str) or not invite_code.strip():
        raise InviteCodeMissingException()

    normalized_invite_code = invite_code.strip()
    if INVITE_CODE_PATTERN.fullmatch(normalized_invite_code) is None:
        raise InviteCodeInvalidException()

    return normalized_invite_code


def _generate_invite_code() -> str:
    # 영어 대문자와 숫자로 6자리로 조합하여 초대코드 생성
    return "".join(
        secrets.choice(INVITE_CODE_ALPHABET)
        for _ in range(INVITE_CODE_LENGTH)
    )


def create_room(
    db: Session,
    *,
    user_id: UUID,
    request: CreateRoomRequest | None,
) -> CreateRoomResponse:
    if request is None:
        raise RoomRequestBodyMissingException()

    room_name = _validate_room_name(request.room_name)
    room_color = _validate_room_color(request.room_color)

    try:
        _ensure_active_user(
            db,
            user_id=user_id,
            use_detailed_status_error=True,
        )

        room = None
        for _ in range(INVITE_CODE_GENERATION_ATTEMPTS):
            invite_code = _generate_invite_code()

            try:
                # 방과 HOST 멤버는 반드시 함께 저장, 한쪽이라도 실패하면 전체 rollback
                # 초대 코드 충돌 시, 새 코드로 재시도
                with db.begin_nested():
                    room = create_room_with_host(
                        db=db,
                        user_id=user_id,
                        room_name=room_name,
                        room_color=room_color,
                        invite_code=invite_code,
                    )
                break
            except IntegrityError as exc:
                if _get_constraint_name(exc) != "uq_rooms_invite_code":
                    raise
                room = None

        if room is None:
            db.rollback()
            raise RoomCreateFailedException()

        room_id = room.id
        room_invite_code = room.invite_code
        db.commit()

        return CreateRoomResponse(
            room_id=room_id,
            invite_code=room_invite_code,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise RoomCreateFailedException() from exc


def get_room_invite_code(
    db: Session,
    *,
    user_id: UUID,
    room_id: str,
) -> InviteCodeResponse:
    parsed_room_id = _parse_room_id(room_id)

    try:
        _ensure_active_user(db, user_id=user_id)

        room = find_room_by_id(
            db=db,
            room_id=parsed_room_id,
        )
        if room is None:
            raise RoomNotFoundException()

        # 방 멤버만 초대코드 접근 가능
        room_member = find_active_room_member(
            db=db,
            room_id=parsed_room_id,
            user_id=user_id,
        )
        if room_member is None:
            raise RoomAccessDeniedException()

        return InviteCodeResponse(
            invite_code=room.invite_code,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise InviteCodeLookupFailedException() from exc


def join_room_by_invite_code(
    db: Session,
    *,
    user_id: UUID,
    request: JoinRoomRequest | None,
) -> JoinRoomResponse:
    if request is None:
        raise RoomRequestBodyMissingException()

    invite_code = _validate_invite_code(request.invite_code)

    try:
        _ensure_active_user(db, user_id=user_id)

        # 삭제된 방은 가입 불가
        room = find_room_by_invite_code(
            db=db,
            invite_code=invite_code,
        )
        if room is None:
            raise InviteCodeRoomNotFoundException()

        existing_member = find_active_room_member(
            db=db,
            room_id=room.id,
            user_id=user_id,
        )
        if existing_member is not None:
            raise RoomAlreadyJoinedException()

        # 초대 코드로 가입한 사용자는 항상 MEMBER로 생성
        create_room_member(
            db=db,
            room_id=room.id,
            user_id=user_id,
        )
        joined_room_id = room.id
        db.commit()

        return JoinRoomResponse(
            room_id=joined_room_id,
        )
    except IntegrityError as exc:
        db.rollback()
        if _get_constraint_name(exc) == "uq_room_members_room_user":
            raise RoomAlreadyJoinedException() from exc
        raise RoomJoinFailedException() from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise RoomJoinFailedException() from exc
