import logging
from fastapi import Request
from app.cache.redis_client import redis_client
logger = logging.getLogger("linkforge.ratelimit")


def client_ip(request: Request) -> str:
    # Behind a proxy this will be the proxy's address.
    return request.client.host if request.client else "unknown"


async def hit(key: str, limit: int, window: int) -> tuple[bool, int, int]:
    """
    Count one request against `key`.
    Returns (allowed, remaining, seconds_until_reset).
    """
    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)  # no await: these are only queued
            pipe.expire(key, window, nx=True)  # set the countdown only on the first hit
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()  # all three run together, atomically
    except Exception as e:
        # Redis is optional (same rule as the cache): fail OPEN
        logger.warning("Rate limiter unavailable, letting request through: %s", e)
        return True, limit, window

    if ttl < 0:  # safety net: the key somehow has no countdown
        ttl = window
    return count <= limit, max(limit - count, 0), ttl
