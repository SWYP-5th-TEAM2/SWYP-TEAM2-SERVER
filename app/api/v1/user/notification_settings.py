from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.user import UpdateNotificationSettingsRequest
from app.services.user import (
    get_notification_settings,
    update_notification_settings,
)

router = APIRouter(
    prefix="/me/notification-settings",
)


@router.get(
    "",
    summary="알림 설정 조회",
    description="로그인한 사용자의 알림 설정을 조회합니다.",
)
def get_my_notification_settings(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_notification_settings(
        db=db,
        user_id=user_id,
    )
    return success_response(
        data=response,
        message="알림 설정 조회 성공",
    )


@router.patch(
    "",
    summary="알림 설정 수정",
    description="로그인한 사용자의 알림 설정을 수정합니다.",
)
def update_my_notification_settings(
    request: UpdateNotificationSettingsRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = update_notification_settings(
        db=db,
        user_id=user_id,
        request=request,
    )
    return success_response(
        data=response,
        message="알림 설정 수정 성공",
    )
