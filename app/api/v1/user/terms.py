from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.core.security.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.user import AgreeTermsRequest
from app.services.user import agree_terms

router = APIRouter()


@router.post(
    "/me/terms",
    summary="약관 동의",
    description="로그인한 사용자의 활성 약관 동의 정보를 저장합니다.",
)
def agree_my_terms(
    request: AgreeTermsRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    agree_terms(
        db=db,
        user_id=user_id,
        request=request,
    )

    return success_response(
        data=None,
        message="약관 동의 성공",
    )
