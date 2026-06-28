from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DeviceTypeMissingException,
    FcmTokenBlankException,
    FcmTokenMissingException,
    ForbiddenException,
    UnsupportedDeviceTypeException,
    UserNotFoundException,
)
from app.models import DeviceType
from app.models.user.enums import UserAccountStatus
from app.repository.fcm import save_user_fcm_token
from app.repository.user import find_user_by_id
from app.schemas.user import SaveFcmTokenResponse


def _validate_fcm_token(fcm_token: str | None) -> str:
    if fcm_token is None:
        raise FcmTokenMissingException()

    normalized_token = fcm_token.strip()
    if not normalized_token:
        raise FcmTokenBlankException()

    return normalized_token


def _parse_device_type(device_type: str | None) -> DeviceType:
    if device_type is None:
        raise DeviceTypeMissingException()

    try:
        return DeviceType(device_type)
    except ValueError:
        raise UnsupportedDeviceTypeException()


def save_fcm_token(
    db: Session,
    *,
    user_id: UUID,
    fcm_token: str | None,
    device_type: str | None,
) -> SaveFcmTokenResponse:
    validated_fcm_token = _validate_fcm_token(fcm_token)
    validated_device_type = _parse_device_type(device_type)

    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundException()

    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    user_fcm_token = save_user_fcm_token(
        db=db,
        user_id=user_id,
        fcm_token=validated_fcm_token,
        device_type=validated_device_type,
    )

    db.commit()
    db.refresh(user_fcm_token)

    return SaveFcmTokenResponse(
        fcm_token_id=user_fcm_token.id,
    )
