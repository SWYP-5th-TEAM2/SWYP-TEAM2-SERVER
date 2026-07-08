from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database.session import get_db
from app.services.common import get_active_terms

router = APIRouter()


@router.get(
    "/terms",
    summary="약관 조회",
    description="활성화된 약관 목록을 조회합니다.",
)
def get_terms(
    db: Session = Depends(get_db),
):
    response = get_active_terms(db)

    return success_response(
        data=response,
        message="약관 조회 성공",
    )
