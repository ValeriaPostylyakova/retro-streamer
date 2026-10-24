from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.redis_client import get_async_redis_client
from app.core.s3_client import S3AsyncService, get_s3_async_client
from app.game_renders.repositories import (
    GameRenderRepository,
)
from app.game_renders.services import GameRenderService
from app.game_renders.services.websocket_service import GameRenderWebSocketService
from app.leaderboard.dependencies import (
    get_leaderboard_service,
)
from app.leaderboard.services import LeaderboardService


def get_game_render_repository(
    db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GameRenderRepository:
    return GameRenderRepository(db_session)


async def get_game_render_service(
    redis_client: Redis = Depends(get_async_redis_client),
    s3_client: S3AsyncService = Depends(get_s3_async_client),
    repository: GameRenderRepository = Depends(get_game_render_repository),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
) -> GameRenderService:
    return GameRenderService(
        redis_client=redis_client,
        s3_client=s3_client,
        repository=repository,
        leaderboard_service=leaderboard_service,
    )


async def get_game_render_websocket_service(
    redis_client: Redis = Depends(get_async_redis_client),
    game_render_service: GameRenderService = Depends(get_game_render_service),
) -> GameRenderWebSocketService:
    return GameRenderWebSocketService(
        redis_client=redis_client,
        render_service=game_render_service,
    )
