from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DeviceType, UserFcmToken


def find_fcm_token_by_token(
    db: Session,
    *,
    fcm_token: str,
) -> UserFcmToken | None:
    stmt = select(UserFcmToken).where(UserFcmToken.fcm_token == fcm_token)
    result = db.execute(stmt)
    return result.scalar_one_or_none()


def save_user_fcm_token(
    db: Session,
    *,
    user_id: UUID,
    fcm_token: str,
    device_type: DeviceType,
) -> UserFcmToken:
    user_fcm_token = find_fcm_token_by_token(
        db=db,
        fcm_token=fcm_token,
    )

    # 동일한 FCM 토큰은 중복 생성하지 않고 최신 사용자와 기기 정보로 활성화한다.
    if user_fcm_token is None:
        user_fcm_token = UserFcmToken(
            user_id=user_id,
            fcm_token=fcm_token,
            device_type=device_type,
            is_active=True,
        )
        db.add(user_fcm_token)
    else:
        user_fcm_token.user_id = user_id
        user_fcm_token.device_type = device_type
        user_fcm_token.is_active = True

    db.flush()
    return user_fcm_token


def find_active_fcm_token_rows(
    db: Session,
    *,
    user_ids: list[UUID],
    notification_type=None,
) -> list[tuple[UUID, str]]:
    if not user_ids:
        return []

    from app.models import NotificationType, User
    from app.models.user.enums import UserAccountStatus

    conditions = [
        UserFcmToken.user_id.in_(user_ids),
        UserFcmToken.is_active.is_(True),
        UserFcmToken.deleted_at.is_(None),
        User.id == UserFcmToken.user_id,
        User.deleted_at.is_(None),
        User.status == UserAccountStatus.ACTIVE,
    ]

    if notification_type == NotificationType.PLAN_REQUESTED:
        conditions.append(User.candidate_place_enabled.is_(True))
    elif notification_type == NotificationType.RESPONSE_DEADLINE_SOON:
        conditions.append(User.vote_deadline_enabled.is_(True))
    elif notification_type == NotificationType.PLAN_CONFIRMED:
        conditions.append(User.schedule_confirmed_enabled.is_(True))

    stmt = select(UserFcmToken.user_id, UserFcmToken.fcm_token).where(*conditions)
    return [(user_id, token) for user_id, token in db.execute(stmt).all()]


def deactivate_fcm_tokens(
    db: Session,
    *,
    fcm_tokens: list[str],
) -> int:
    if not fcm_tokens:
        return 0
    stmt = select(UserFcmToken).where(UserFcmToken.fcm_token.in_(fcm_tokens))
    rows = list(db.execute(stmt).scalars().all())
    for row in rows:
        row.is_active = False
    db.flush()
    return len(rows)
