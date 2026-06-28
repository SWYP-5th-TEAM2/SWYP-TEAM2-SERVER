from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    NotificationSettingsFailedException,
    NotificationSettingsRequestBodyMissingException,
    NotificationSettingsUpdateFieldsMissingException,
    NotificationSettingValueInvalidException,
    UnsupportedNotificationSettingException,
    UserNotFoundException,
)
from app.models import User
from app.models.user.enums import UserAccountStatus
from app.repository.user import find_user_by_id
from app.schemas.user import (
    NotificationSettingsResponse,
    UpdateNotificationSettingsRequest,
)

NOTIFICATION_SETTING_FIELDS = frozenset(
    {
        "candidate_place_enabled",
        "vote_deadline_enabled",
        "schedule_confirmed_enabled",
        "quiet_recommendation_enabled",
    },
)


def _ensure_active_user(db: Session, user_id: UUID) -> User:
    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundException()

    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    return user


def _to_notification_settings_response(
    user: User,
) -> NotificationSettingsResponse:
    return NotificationSettingsResponse(
        candidate_place_enabled=user.candidate_place_enabled,
        vote_deadline_enabled=user.vote_deadline_enabled,
        schedule_confirmed_enabled=user.schedule_confirmed_enabled,
        quiet_recommendation_enabled=user.quiet_recommendation_enabled,
    )


def get_notification_settings(
    db: Session,
    *,
    user_id: UUID,
) -> NotificationSettingsResponse:
    try:
        # 조회 전 사용자 존재 여부와 활성 상태를 공통 검증
        user = _ensure_active_user(db, user_id)
        return _to_notification_settings_response(user)
    except SQLAlchemyError as exc:
        raise NotificationSettingsFailedException() from exc


def update_notification_settings(
    db: Session,
    *,
    user_id: UUID,
    request: UpdateNotificationSettingsRequest | None,
) -> NotificationSettingsResponse:
    if request is None:
        raise NotificationSettingsRequestBodyMissingException()

    if request.model_extra:
        raise UnsupportedNotificationSettingException()

    # 실제 전달된 필드만 수정하며 빈 객체는 허용하지 않음
    provided_fields = request.model_fields_set & NOTIFICATION_SETTING_FIELDS
    if not provided_fields:
        raise NotificationSettingsUpdateFieldsMissingException()

    # 실제 JSON boolean만 허용
    for field_name in provided_fields:
        if type(getattr(request, field_name)) is not bool:
            raise NotificationSettingValueInvalidException()

    try:
        user = _ensure_active_user(db, user_id)

        for field_name in provided_fields:
            setattr(user, field_name, getattr(request, field_name))

        response = _to_notification_settings_response(user)
        db.commit()
        return response
    except SQLAlchemyError as exc:
        db.rollback()
        raise NotificationSettingsFailedException() from exc
