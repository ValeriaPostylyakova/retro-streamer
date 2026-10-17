import redis
import redis.asyncio as aioredis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

redis_async_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

redis_sync_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=False,
)


def get_async_redis_client() -> AsyncRedis:
    return redis_async_client


def get_sync_redis_client() -> redis.Redis:
    return redis_sync_client
