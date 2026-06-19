from typing import Any

from redis.asyncio import Redis

from app.core.exceptions import InvalidTokenException, RefreshTokenReusedException
from app.core.security.jwt import decode_refresh_token, get_subject, get_session_id, get_jti, rotate_tokens, \
    get_expires_at
from app.core.security.token_store import get_refresh_session, update_refresh_session_jti, delete_refresh_session, \
    blacklist_access_token
from app.schemas.auth import TokenResponse


async def reissue_tokens(
    redis: Redis,
    refresh_token: str,
) -> TokenResponse:
    refresh_payload = decode_refresh_token(refresh_token)

    user_id = get_subject(refresh_payload)
    session_id = get_session_id(refresh_payload)
    refresh_jti = get_jti(refresh_payload)
    print("old refresh jti:", refresh_jti)
    print("session id:", session_id)

    # redis session id 조회
    refresh_session = await get_refresh_session(
        redis=redis,
        session_id=session_id,
    )

    if refresh_session is None:
        raise InvalidTokenException()

    stored_user_id = refresh_session["user_id"]
    stored_jti = refresh_session["current_jti"]

    if stored_user_id != str(user_id):
        raise InvalidTokenException()

    if stored_jti != refresh_jti:
        await delete_refresh_session(
            redis=redis,
            session_id=session_id,
        )
        raise RefreshTokenReusedException()

    # 기존 user id, session id 기반 토큰 재발급(RTR, Sliding Expiration)
    tokens = rotate_tokens(
        user_id=user_id,
        session_id=session_id,
    )

    new_refresh_payload = decode_refresh_token(tokens.refresh_token)
    new_refresh_jti = get_jti(new_refresh_payload)
    print("new refresh jti:", new_refresh_jti)

    # Redis token 업데이트
    await update_refresh_session_jti(
        redis=redis,
        session_id=session_id,
        user_id=user_id,
        new_jti=new_refresh_jti,
    )

    return tokens


async def logout_token(
    redis: Redis,
    *,
    access_payload: dict[str, Any],
    refresh_token: str,
) -> None:
    access_jti = get_jti(access_payload)
    access_expires_at = get_expires_at(access_payload)

    refresh_payload = decode_refresh_token(refresh_token)
    session_id = get_session_id(refresh_payload)

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