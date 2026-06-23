from redis.asyncio import Redis

from app.config import settings
from app.core.exceptions import RedisUnavailableException

redis_client: Redis | None = None

async def connect_redis() -> None:
    global redis_client

    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
    )

    try:
        await redis_client.ping()
    except Exception:
        redis_client = None
        raise RedisUnavailableException()


async def close_redis() -> None:
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> Redis:
    if redis_client is None:
        raise RedisUnavailableException()

    return redis_client