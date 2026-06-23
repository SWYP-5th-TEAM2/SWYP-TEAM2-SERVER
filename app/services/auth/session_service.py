from typing import Any

from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenException, RefreshTokenReusedException, ForbiddenException
from app.core.security.jwt import decode_refresh_token, get_subject, get_session_id, get_jti, rotate_tokens, \
    get_expires_at
from app.core.security.token_store import update_refresh_session_jti, delete_refresh_session, \
    blacklist_access_token, get_refresh_session
from app.models.user.enums import UserAccountStatus
from app.repository.user import find_user_by_id
from app.schemas.auth import TokenResponse


async def reissue_tokens(
    db: Session,
    redis: Redis,
    refresh_token: str,
) -> TokenResponse:
    refresh_payload = decode_refresh_token(refresh_token)

    user_id = get_subject(refresh_payload)
    session_id = get_session_id(refresh_payload)
    refresh_jti = get_jti(refresh_payload)

    user = find_user_by_id(db=db, user_id=user_id)

    if user is None:
        await delete_refresh_session(
            redis=redis,
            session_id=session_id,
        )

    if user.status != UserAccountStatus.ACTIVE:
        await delete_refresh_session(
            redis=redis,
            session_id=session_id,
        )
        raise ForbiddenException()

    # 기존 user id, session id 기반 토큰 재발급(RTR, Sliding Expiration)
    tokens = rotate_tokens(
        user_id=user_id,
        session_id=session_id,
    )

    new_refresh_payload = decode_refresh_token(tokens.refresh_token)
    new_refresh_jti = get_jti(new_refresh_payload)

    # Redis token 업데이트
    result = await update_refresh_session_jti(
        redis=redis,
        session_id=session_id,
        user_id=user_id,
        new_jti=new_refresh_jti,
        old_jti=refresh_jti,
    )
    print("rotate refresh session result:", result)
    print("user_id:", user_id)
    print("session_id:", session_id)
    print("old_jti:", refresh_jti)
    print("new_jti:", new_refresh_jti)

    if result in {"missing", "invalid", "invalid_user"}:
        raise InvalidTokenException()

    if result == "reused":
        raise RefreshTokenReusedException()

    if result != "rotated":
        raise InvalidTokenException()

    return tokens


async def logout_token(
    redis: Redis,
    *,
    access_payload: dict[str, Any],
    refresh_token: str,
) -> None:
    access_user_id = get_subject(access_payload)
    access_jti = get_jti(access_payload)
    access_expires_at = get_expires_at(access_payload)

    refresh_payload = decode_refresh_token(refresh_token)
    refresh_user_id = get_subject(refresh_payload)
    session_id = get_session_id(refresh_payload)

    if str(access_user_id) != str(refresh_user_id):
        raise InvalidTokenException()

    refresh_session = await get_refresh_session(
        redis=redis,
        session_id=session_id,
    )

    if refresh_session is None:
        raise InvalidTokenException()

    if refresh_session["user_id"] != str(access_user_id):
        raise InvalidTokenException()

    # blacklist access token
    await blacklist_access_token(
        redis=redis,
        jti=access_jti,
        expires_at=access_expires_at,
    )

    # delete refresh session
    await delete_refresh_session(
        redis=redis,
        session_id=session_id,
    )