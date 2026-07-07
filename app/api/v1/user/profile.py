from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.user import UpdateUserProfileRequest
from app.services.user import (
    get_user_onboarding_status,
    get_user_profile,
    update_user_profile,
)

router = APIRouter()


@router.patch(
    "/me",
    summary="사용자 정보 수정",
    description="로그인한 사용자의 닉네임과 프로필 이미지를 수정합니다.",
)
def update_my_profile(
    request: UpdateUserProfileRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = update_user_profile(
        db=db,
        user_id=user_id,
        request=request,
    )

    return success_response(
        data=response,
        message="프로필 수정 성공",
    )


@router.get(
    "/me",
    summary="사용자 정보 조회",
    description="로그인한 사용자의 프로필과 참여 중인 방 정보를 조회합니다.",
)
def get_my_profile(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_user_profile(
        db=db,
        user_id=user_id,
    )

    return success_response(
        data=response,
        message="사용자 정보 조회 성공",
    )


@router.get(
    "/me/onboarding",
    summary="온보딩 완료 여부 확인",
    description="로그인한 사용자의 온보딩 완료 여부를 조회합니다.",
)
def get_my_onboarding_status(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    response = get_user_onboarding_status(
        db=db,
        user_id=user_id,
    )

    return success_response(
        data=response,
        message="온보딩 확인 성공",
    )
