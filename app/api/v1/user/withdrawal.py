from typing import Any

from fastapi import APIRouter, Body, Depends
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.redis import get_redis
from app.core.responses import success_response
from app.core.security.dependencies import get_current_access_payload
from app.core.security.jwt import get_subject
from app.database.session import get_db
from app.schemas.user import UserWithdrawalRequest
from app.services.user import withdraw_user

router = APIRouter()


@router.delete(
    "/me",
    summary="회원탈퇴",
    description="로그인한 사용자의 계정과 관련 데이터를 탈퇴 처리합니다.",
)
async def withdraw_my_account(
    request: UserWithdrawalRequest | None = Body(default=None),
    access_payload: dict[str, Any] = Depends(get_current_access_payload),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    await withdraw_user(
        db=db,
        redis=redis,
        user_id=get_subject(access_payload),
        access_payload=access_payload,
        request=request,
    )
    return success_response(
        data=None,
        message="회원탈퇴 성공",
    )
