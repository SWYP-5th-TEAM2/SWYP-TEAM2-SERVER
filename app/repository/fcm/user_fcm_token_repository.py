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
