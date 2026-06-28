from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.user import SaveFcmTokenRequest
from app.services.user import save_fcm_token

router = APIRouter()


@router.post(
    "/me/fcm-token",
    summary="FCM 토큰 저장",
    description="로그인한 사용자의 FCM 토큰을 저장합니다.",
)
def save_my_fcm_token(
    request: SaveFcmTokenRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = save_fcm_token(
        db=db,
        user_id=user_id,
        fcm_token=request.fcm_token if request else None,
        device_type=request.device_type if request else None,
    )

    return success_response(
        data=response,
        message="FCM 토큰 저장 완료",
    )
