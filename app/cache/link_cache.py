import logging

from app.cache.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger("linkforge.cache")


def _key(short_code: str) -> str:
    return f"link:{short_code}"  # f-string: link:KpDbL6H


async def get_url(short_code: str) -> str | None:
    try:
        return await redis_client.get(_key(short_code))  # None if the key is missing
    except Exception as e:
        # Redis down? Pretend it's a miss. The caller falls back to Postgres.
        logger.warning("Redis GET failed: %s", e)
        return None


async def set_url(short_code: str, url: str) -> None:
    try:
        await redis_client.set(
            _key(short_code), url, ex=settings.LINK_CACHE_TTL_SECONDS
        )
    except Exception as e:
        logger.warning("Redis SET failed: %s", e)


async def delete_url(short_code: str) -> None:  # used in step 4
    try:
        await redis_client.delete(_key(short_code))
    except Exception as e:
        logger.warning("Redis DEL failed: %s", e)
