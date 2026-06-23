from typing import Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis

from app.core.exceptions import TokenMissingException, LoggedOutTokenException
from app.core.redis import get_redis
from app.core.security.jwt import decode_access_token, get_subject, get_jti
from app.core.security.token_store import is_access_token_blacklisted

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_access_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    if credentials is None:
        raise TokenMissingException()

    token = credentials.credentials
    payload = decode_access_token(token)

    access_jti = get_jti(payload)
    is_blacklisted = await is_access_token_blacklisted(
        redis=redis,
        jti=access_jti,
    )

    if is_blacklisted:
        raise LoggedOutTokenException()

    return payload


async def get_current_user_id(
    payload: dict[str, Any] = Depends(get_current_access_payload),
) -> UUID:
    return get_subject(payload=payload)