import logging

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.auth.dependencies import CurrentUser
from app.core.redis_client import get_async_redis_client

logger = logging.getLogger(__name__)

ROLE_LIMITS = {
    "default": {"requests": 10, "window": 60},
    "premium": {"requests": 30, "window": 60},
}


async def role_rate_limiter(
    request: Request,
    current_user: CurrentUser,
    redis_client: Redis = Depends(get_async_redis_client),
):
    role = current_user.role
    user_id = current_user.id

    limit_config = ROLE_LIMITS.get(role)
    if limit_config is None:
        return True

    max_requests = limit_config["requests"]
    window = limit_config["window"]
    redis_key = f"rate_limit:user:{user_id}"

    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            current_requests, ttl = await pipe.execute()

        if current_requests == 1 or ttl == -1:
            await redis_client.expire(redis_key, window)
            ttl = window

        if current_requests > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too Many Requests",
                    "message": (f"Вы превысили лимит запросов для роли '{role}'."),
                    "retry_after_seconds": ttl if ttl > 0 else window,
                },
            )

    except RedisError as exc:
        logger.error("Redis rate limiter error: %s", exc)
        return True

    return True
