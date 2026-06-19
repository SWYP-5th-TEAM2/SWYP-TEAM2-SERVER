from typing import Any

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.exceptions import UnsupportedProviderException
from app.core.redis import get_redis
from app.core.responses import success_response
from app.core.security.dependencies import get_current_access_payload
from app.database.session import get_db
from app.models.user.enums import Provider
from app.schemas.auth import ReissueRequest, LogoutRequest, SocialLoginRequest
from app.services.auth import reissue_tokens, logout_token
from app.services.auth.social_login import social_login

router = APIRouter()

def parse_provider(provider: str) -> Provider:
    try:
        return Provider(provider.upper())
    except ValueError:
        raise UnsupportedProviderException()

@router.post(
    "/login/{provider}",
    summary="소셜 로그인",
    description="소셜로그인 제공자(kakao, google, apple) 인가 코드로 로그인\n신규 회원은 회원 등록을 진행합니다.\n",
)
async def login(
    provider: str,
    request: SocialLoginRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    login_response = await social_login(
        db=db,
        redis=redis,
        provider=parse_provider(provider),
        code=request.code,
    )

    return success_response(
        data=login_response,
        message="로그인 성공",
    )


@router.post(
    "/reissue",
    summary="토큰 재발급",
    description="Refresh Token으로 새로운 Access Token과 Refresh Token을 재발급합니다.\n기존 Refresh Token은 사용할 수 없습니다.",
)
async def reissue_token(
    request: ReissueRequest,
    redis: Redis = Depends(get_redis),
):
    tokens = await reissue_tokens(
        redis=redis,
        refresh_token=request.refresh_token,
    )

    return success_response(
        data=tokens,
        message="토큰 재발급 성공"
    )

@router.post(
    "/logout",
    summary="로그아웃",
    description="Access Token을 블랙리스트에 등록하고, Refresh Token 세션을 삭제합니다.",
)
async def logout(
    request: LogoutRequest,
    access_payload: dict[str, Any] = Depends(get_current_access_payload),
    redis: Redis = Depends(get_redis),
 ):
    await logout_token(
        redis=redis,
        access_payload=access_payload,
        refresh_token=request.refresh_token,
    )

    return success_response(
        data=None,
        message="로그아웃 성공",
    )