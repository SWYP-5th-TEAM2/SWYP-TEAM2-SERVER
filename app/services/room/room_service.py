import re
import secrets
import string
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppException,
    BlockedRoomUserException,
    ForbiddenException,
    InviteCodeInvalidException,
    InviteCodeLookupFailedException,
    InviteCodeMissingException,
    InviteCodeRoomNotFoundException,
    MyRoomsLookupFailedException,
    RoomAccessDeniedException,
    RoomAlreadyJoinedException,
    RoomAlreadyLeftException,
    RoomColorInvalidException,
    RoomColorMissingException,
    RoomCreateFailedException,
    RoomIdInvalidException,
    RoomInfoLookupFailedException,
    RoomJoinFailedException,
    RoomLeaveFailedException,
    RoomHostRequiredException,
    RoomMemberAlreadyKickedException,
    RoomMemberKickFailedException,
    RoomMemberNotFoundException,
    RoomMemberUserIdInvalidException,
    RoomNameInvalidException,
    RoomNameMissingException,
    RoomNameTooLongException,
    RoomNotFoundException,
    RoomRequestBodyMissingException,
    RoomUnavailableException,
    SelfKickNotAllowedException,
    HostKickNotAllowedException,
    UserNotFoundException,
    WithdrawnRoomUserException,
)
from app.models import RoomMember, RoomMemberRole, User
from app.models.user.enums import UserAccountStatus
from app.repository.room import (
    count_active_places_by_room_id,
    count_active_room_members,
    count_votes_by_plan_id,
    create_room_member,
    create_room_with_host,
    find_active_room_by_id_for_update,
    find_active_room_by_invite_code_for_update,
    find_active_room_member,
    find_earliest_active_member,
    find_my_active_rooms,
    find_random_room_member_preview_names,
    find_representative_plan_by_room_id,
    find_room_by_id,
    find_room_by_id_including_deleted,
    find_room_member,
    find_room_member_details,
)
from app.repository.user import find_user_by_id
from app.schemas.room import (
    CreateRoomRequest,
    CreateRoomResponse,
    InviteCodeResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    MyRoomsResponse,
    MyRoomSummaryResponse,
    RoomDetailResponse,
    RoomMemberResponse,
)

MAX_ROOM_NAME_LENGTH = 12
INVITE_CODE_LENGTH = 6
INVITE_CODE_ALPHABET = string.ascii_uppercase + string.digits
INVITE_CODE_GENERATION_ATTEMPTS = 10

ROOM_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
INVITE_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6}$")
ROOM_MEMBER_PREVIEW_LIMIT = 3


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


def _parse_room_member_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except (TypeError, ValueError):
        raise RoomMemberUserIdInvalidException()


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
        room = find_active_room_by_invite_code_for_update(
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


def get_room_detail(
    db: Session,
    *,
    user_id: UUID,
    room_id: str,
) -> RoomDetailResponse:
    parsed_room_id = _parse_room_id(room_id)

    try:
        _ensure_active_user(db, user_id=user_id)

        # 삭제된 방 포함 조회
        room = find_room_by_id_including_deleted(
            db=db,
            room_id=parsed_room_id,
        )
        if room is None:
            raise RoomNotFoundException()
        if room.deleted_at is not None:
            raise RoomUnavailableException()

        # 활성 RoomMember만 접근 가능
        current_member = find_active_room_member(
            db=db,
            room_id=parsed_room_id,
            user_id=user_id,
        )
        if current_member is None:
            raise RoomAccessDeniedException()

        # 멤버 정보와 프로필 이미지 조회
        member_rows = find_room_member_details(
            db=db,
            room_id=parsed_room_id,
        )
        # 저장된 장소 개수 조회
        place_count = count_active_places_by_room_id(
            db=db,
            room_id=parsed_room_id,
        )

        return RoomDetailResponse(
            room_id=room.id,
            room_name=room.name,
            member_count=len(member_rows),
            place_count=place_count,
            members=[
                RoomMemberResponse(
                    user_id=member_id,
                    profile_image=profile_image,
                    nickname=nickname,
                    role=role.value,
                )
                for member_id, profile_image, nickname, role in member_rows
            ],
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise RoomInfoLookupFailedException() from exc


def get_my_rooms(
    db: Session,
    *,
    user_id: UUID,
    keyword: str | None,
) -> MyRoomsResponse:
    normalized_keyword = keyword.strip() if keyword is not None else None
    if normalized_keyword == "":
        normalized_keyword = None

    try:
        _ensure_active_user(
            db,
            user_id=user_id,
            use_detailed_status_error=True,
        )

        rooms = find_my_active_rooms(
            db=db,
            user_id=user_id,
            keyword=normalized_keyword,
        )
        current_time = datetime.now(timezone.utc)

        room_summaries: list[MyRoomSummaryResponse] = []
        for room in rooms:
            # 우선순위는 VOTING(마감 임박) > CONFIRMED > COMPLETED > null
            representative_plan = find_representative_plan_by_room_id(
                db=db,
                room_id=room.id,
                current_time=current_time,
            )
            vote_member_count = (
                count_votes_by_plan_id(
                    db=db,
                    plan_id=representative_plan.id,
                )
                if representative_plan is not None
                else 0
            )

            room_summaries.append(
                MyRoomSummaryResponse(
                    room_id=room.id,
                    room_name=room.name,
                    color=room.color,
                    member_count=count_active_room_members(
                        db=db,
                        room_id=room.id,
                    ),
                    member_preview_names=find_random_room_member_preview_names(
                        db=db,
                        room_id=room.id,
                        limit=ROOM_MEMBER_PREVIEW_LIMIT,
                    ),
                    plan_status=(
                        representative_plan.status.value
                        if representative_plan is not None
                        else None
                    ),
                    vote_member_count=vote_member_count,
                )
            )

        return MyRoomsResponse(rooms=room_summaries)
    except SQLAlchemyError as exc:
        db.rollback()
        raise MyRoomsLookupFailedException() from exc


def _transfer_room_host(
    db: Session,
    *,
    room_id: UUID,
    leaving_host_user_id: UUID,
) -> bool:
    # TODO: 호스트가 나갈 경우 위임하는 로직(추후 개선 필요)
    next_host = find_earliest_active_member(
        db=db,
        room_id=room_id,
        excluded_user_id=leaving_host_user_id,
    )
    if next_host is None:
        return False

    next_host.role = RoomMemberRole.HOST
    return True


def leave_room(
    db: Session,
    *,
    user_id: UUID,
    room_id: str,
) -> None:
    parsed_room_id = _parse_room_id(room_id)

    try:
        _ensure_active_user(db, user_id=user_id)

        room = find_active_room_by_id_for_update(
            db=db,
            room_id=parsed_room_id,
        )
        if room is None:
            raise RoomNotFoundException()

        room_member = find_room_member(
            db=db,
            room_id=parsed_room_id,
            user_id=user_id,
        )
        if room_member is None:
            raise ForbiddenException()
        if room_member.deleted_at is not None:
            raise RoomAlreadyLeftException()

        left_at = datetime.now(timezone.utc)

        if room_member.role == RoomMemberRole.HOST:
            host_transferred = _transfer_room_host(
                db=db,
                room_id=parsed_room_id,
                leaving_host_user_id=user_id,
            )

            # 후임 멤버가 없는 경우 마지막 사용자가 나가는 것이므로 방도 함께 종료
            if not host_transferred:
                room.deleted_at = left_at

        room_member.deleted_at = left_at
        db.commit()
    except AppException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise RoomLeaveFailedException() from exc


def kick_room_member(
    db: Session,
    *,
    requester_user_id: UUID,
    room_id: str,
    target_user_id: str,
) -> None:
    parsed_room_id = _parse_room_id(room_id)
    parsed_target_user_id = _parse_room_member_user_id(target_user_id)

    try:
        _ensure_active_user(db, user_id=requester_user_id)

        room = find_active_room_by_id_for_update(
            db=db,
            room_id=parsed_room_id,
        )
        if room is None:
            raise RoomNotFoundException()

        requester = find_active_room_member(
            db=db,
            room_id=parsed_room_id,
            user_id=requester_user_id,
        )
        if requester is None or requester.role != RoomMemberRole.HOST:
            raise RoomHostRequiredException()

        if requester_user_id == parsed_target_user_id:
            raise SelfKickNotAllowedException()

        target_user = find_user_by_id(
            db=db,
            user_id=parsed_target_user_id,
        )
        if target_user is None:
            raise UserNotFoundException()

        target_member = find_room_member(
            db=db,
            room_id=parsed_room_id,
            user_id=parsed_target_user_id,
        )
        if target_member is None:
            raise RoomMemberNotFoundException()
        if target_member.deleted_at is not None:
            raise RoomMemberAlreadyKickedException()
        if target_member.role == RoomMemberRole.HOST:
            raise HostKickNotAllowedException()

        target_member.deleted_at = datetime.now(timezone.utc)
        db.commit()
    except AppException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise RoomMemberKickFailedException() from exc
