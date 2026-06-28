from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis

from app.core.exceptions import (
    AccessTokenMissingException,
    AuthorizationHeaderMissingException,
    InvalidAccessTokenException,
    LoggedOutTokenException,
)
from app.core.redis import get_redis
from app.core.security.jwt import decode_access_token, get_subject, get_jti
from app.core.security.token_store import is_access_token_blacklisted

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_access_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    authorization = request.headers.get("Authorization")

    if authorization is None:
        raise AuthorizationHeaderMissingException()

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer":
        raise InvalidAccessTokenException()

    if not token.strip():
        raise AccessTokenMissingException()

    if credentials is None:
        raise InvalidAccessTokenException()

    payload = decode_access_token(str(credentials.credentials))

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
