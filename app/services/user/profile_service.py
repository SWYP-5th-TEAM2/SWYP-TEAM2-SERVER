import re
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    InvalidNicknameFormatException,
    InvalidProfileImageUrlException,
    NicknameContainsInvalidCharacterException,
    NicknameTooLongException,
    ProfileImageUrlNotAllowedException,
    ProfileUpdateFailedException,
    ProfileUpdateFieldsMissingException,
    RequestBodyMissingException,
    UserNotFoundException,
)
from app.models import ImagePurpose
from app.models.user.enums import UserAccountStatus
from app.repository.user import (
    count_recurring_schedule_groups_by_user_id,
    demote_user_profile_images_except,
    find_user_image_by_id,
    find_room_summaries_by_user_id,
    find_user_by_id,
    find_user_image_by_url,
)
from app.schemas.user import (
    MyRoomResponse,
    UpdateUserProfileRequest,
    UpdateUserProfileResponse,
    UserProfileResponse,
)

NICKNAME_PATTERN = re.compile(r"^[A-Za-z0-9가-힣]+$")
MAX_NICKNAME_LENGTH = 12


def _validate_nickname(nickname: str | None) -> str:
    # nickname은 DB에서 nullable이지만, 온보딩 이후 프로필 수정에서는 null/공백을 허용하지 않는다.
    if nickname is None or not nickname.strip():
        raise InvalidNicknameFormatException()

    # 화면과 다른 API에서도 동일한 정책을 사용할 수 있도록 길이와 문자 규칙을 서비스에서 검증한다.
    if len(nickname) > MAX_NICKNAME_LENGTH:
        raise NicknameTooLongException()

    if NICKNAME_PATTERN.fullmatch(nickname) is None:
        raise NicknameContainsInvalidCharacterException()

    return nickname


def _validate_profile_image_url(profile_image_url: str) -> str:
    # 공백이 포함되거나 HTTP(S) 형식이 아닌 값은 이미지 조회 전에 형식 오류로 처리한다.
    if any(character.isspace() for character in profile_image_url):
        raise InvalidProfileImageUrlException()

    parsed_url = urlparse(profile_image_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise InvalidProfileImageUrlException()

    return profile_image_url


def _ensure_active_user(db: Session, user_id: UUID):
    # 토큰의 subject가 실제 사용자와 연결되고, 현재 서비스 이용이 가능한 계정인지 확인한다.
    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundException()

    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    return user


def update_user_profile(
    db: Session,
    *,
    user_id: UUID,
    request: UpdateUserProfileRequest | None,
) -> UpdateUserProfileResponse:
    if request is None:
        raise RequestBodyMissingException()

    # nickname은 필수, profileImageUrl은 생략 또는 null(프로필 이미지 제거) 가능
    provided_fields = request.model_fields_set
    if not provided_fields or "nickname" not in provided_fields:
        raise ProfileUpdateFieldsMissingException()

    # 닉네임 형식 검증
    nickname = _validate_nickname(request.nickname)
    profile_image_url_provided = "profile_image_url" in provided_fields

    try:
        user = _ensure_active_user(db, user_id)

        # 현재 연결된 이미지 검사
        current_profile_image = (
            find_user_image_by_id(
                db=db,
                user_id=user_id,
                image_id=user.profile_image_id,
            )
            if user.profile_image_id is not None
            else None
        )

        # profileImageUrl 생략 시, 기존 이미지 유지
        next_profile_image = current_profile_image

        if profile_image_url_provided:
            if request.profile_image_url is None:
                # null 입력 시 프로필 이미지 연결 해제
                next_profile_image = None
            else:
                profile_image_url = _validate_profile_image_url(
                    request.profile_image_url,
                )

                # URL과 user_id가 모두 일치하면 연결
                next_profile_image = find_user_image_by_url(
                    db=db,
                    user_id=user_id,
                    image_url=profile_image_url,
                )
                if next_profile_image is None:
                    raise ProfileImageUrlNotAllowedException()

                if next_profile_image.image_purpose != ImagePurpose.PROFILE_IMAGE:
                    raise ProfileImageUrlNotAllowedException()

            # 선택한 이미지 한 건만 남기고, 같은 사용자의 나머지는 모두 ETC로 변경
            demote_user_profile_images_except(
                db=db,
                user_id=user_id,
                selected_image_id=(
                    next_profile_image.id
                    if next_profile_image is not None
                    else None
                ),
            )

            # null이면 FK는 null, 이미지가 있으면 FK 연결
            user.profile_image_id = (
                next_profile_image.id
                if next_profile_image is not None
                else None
            )

        user.nickname = nickname

        db.commit()

        return UpdateUserProfileResponse(
            nickname=nickname,
            profile_image_url=(
                next_profile_image.image_url
                if next_profile_image is not None
                else None
            ),
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileUpdateFailedException() from exc


def get_user_profile(
    db: Session,
    *,
    user_id: UUID,
) -> UserProfileResponse:
    user = _ensure_active_user(db, user_id)

    # profile_image_id가 있더라도 유효한 이미지만 응답에 포함
    profile_image = (
        find_user_image_by_id(
            db=db,
            user_id=user_id,
            image_id=user.profile_image_id,
        )
        if user.profile_image_id is not None
        else None
    )

    # 참여 ROOM별 멤버 수는 한 번의 GROUP BY 쿼리로 가져와 방마다 추가 조회하는 N+1을 방지
    room_summaries = find_room_summaries_by_user_id(
        db=db,
        user_id=user_id,
    )

    # 반복 일정은 COUNT 결과만 조회
    recurring_schedule_count = count_recurring_schedule_groups_by_user_id(
        db=db,
        user_id=user_id,
    )

    return UserProfileResponse(
        nickname=user.nickname,
        profile_image=profile_image.image_url if profile_image else None,
        email=user.email,
        my_rooms=[
            MyRoomResponse(
                room_id=room_id,
                room_name=room_name,
                member_count=member_count,
            )
            for room_id, room_name, member_count in room_summaries
        ],
        recurring_schedule_count=recurring_schedule_count,
    )
