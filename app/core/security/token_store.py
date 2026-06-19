import json
from datetime import datetime, timezone
from uuid import UUID

from redis.asyncio import Redis

from app.config import settings
from app.core.exceptions import InvalidTokenException

REFRESH_SESSION_KEY_PREFIX = "refresh:session"
ACCESS_BLACKLIST_KEY_PREFIX = "blacklist:access"

def _refresh_session_key(session_id: str) -> str:
    return f"{REFRESH_SESSION_KEY_PREFIX}:{session_id}"

def _access_blacklist_key(jti: str) -> str:
    return f"{ACCESS_BLACKLIST_KEY_PREFIX}:{jti}"

def _seconds_until(expires_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    seconds = int((expires_at - now).total_seconds())
    return max(seconds, 0)

def _refresh_token_ttl_seconds() -> int:
    return settings.refresh_token_expire_days * 24 * 60 * 60


# refresh token - sid, jti 저장 (로그인)
async def save_refresh_session(
    redis: Redis,
    *,
    session_id: str,
    user_id: UUID | str,
    current_jti: str,
) -> None:
    value = {
        "user_id": str(user_id),
        "current_jti": current_jti,
    }

    await redis.set(
        _refresh_session_key(session_id),
        json.dumps(value),
        ex=_refresh_token_ttl_seconds(),
    )


# refresh token - sid로 jti 조회 (재발급)
async def get_refresh_session(
    redis: Redis,
    *,
    session_id: str,
) -> dict[str, str] | None:
    value = await redis.get(_refresh_session_key(session_id))

    if value is None:
        return None

    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        raise InvalidTokenException()

    user_id = data.get("user_id")
    current_jti = data.get("current_jti")

    if not isinstance(user_id, str) or not isinstance(current_jti, str):
        raise InvalidTokenException()

    return {
        "user_id": user_id,
        "current_jti": current_jti,
    }


# refresh token - RTR 시 jti 업데이트, sid 유지 (재발급)
async def update_refresh_session_jti(
    redis: Redis,
    *,
    session_id: str,
    user_id: UUID | str,
    new_jti: str,
) -> None:
    await save_refresh_session(
        redis,
        session_id=session_id,
        user_id=user_id,
        current_jti=new_jti,
    )


# refresh token - sid 삭제 (로그아웃)
async def delete_refresh_session(
    redis: Redis,
    *,
    session_id: str,
) -> None:
    await redis.delete(_refresh_session_key(session_id))


# access token - blacklist 등록 (로그아웃)
async def blacklist_access_token(
    redis: Redis,
    *,
    jti: str,
    expires_at: datetime,
) -> None:
    ttl = _seconds_until(expires_at)

    if ttl <= 0:
        return

    await redis.set(
        _access_blacklist_key(jti),
        "1",
        ex=ttl,
    )


# access token - blacklist 체크
async def is_access_token_blacklisted(
    redis: Redis,
    *,
    jti: str,
) -> bool:
    exists = await redis.exists(_access_blacklist_key(jti))
    return exists == 1