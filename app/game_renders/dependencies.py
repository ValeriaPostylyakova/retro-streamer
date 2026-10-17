from fastapi import Depends
from redis.asyncio import Redis

from app.core.redis_client import get_async_redis_client
from app.core.s3_client import S3AsyncService, get_s3_async_client
from app.game_renders.services import GameRenderService


async def get_game_render_service(
    redis_client: Redis = Depends(get_async_redis_client),
    s3_client: S3AsyncService = Depends(get_s3_async_client),
) -> GameRenderService:
    return GameRenderService(redis_client=redis_client, s3_client=s3_client)
