import hashlib
from uuid import UUID

from celery.result import AsyncResult
from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.core.s3_client import S3AsyncService
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.repositories import GameRenderRepository
from app.game_renders.schemas import (
    GameInfoResponse,
    GameInitialState,
    GameRenderRequest,
    GameRenderResponse,
    GameRules,
    RenderStatus,
    TaskStatusResponse,
)
from app.game_renders.tasks.generate_game_gif import generate_game_gif


class GameRenderService:
    def __init__(
        self,
        redis_client: Redis,
        s3_client: S3AsyncService,
        repository: GameRenderRepository,
    ):
        self.redis_client = redis_client
        self.s3_client = s3_client
        self.repository = repository

    def _generate_idempotency_hash(
        self,
        request_data: GameRenderRequest,
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{request_data.seed}:{commands_str}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(
        self,
        user_id: UUID,
        request_data: GameRenderRequest,
    ) -> GameRenderResponse:
        hash_key = self._generate_idempotency_hash(request_data)

        cache_key = RedisKeyManager.game_cache(hash_key)
        lock_key = RedisKeyManager.render_lock(hash_key)

        cached_s3_key = await self.redis_client.get(cache_key)
        if cached_s3_key:
            if cached_s3_key == "PENDING":
                return GameRenderResponse(status=RenderStatus.PENDING, cached=True)

            s3_download_url = await self.s3_client.get_file_url(
                str(cached_s3_key), is_public=False
            )
            return GameRenderResponse(
                status=RenderStatus.SUCCESS, download_url=s3_download_url, cached=True
            )

        db_record = await self.repository.get_render_by_commands_hash(
            commands_hash=hash_key
        )
        if db_record:
            await self.redis_client.set(cache_key, db_record.s3_key, ex=86400)
            s3_download_url = await self.s3_client.get_file_url(
                db_record.s3_key, is_public=False
            )
            return GameRenderResponse(
                status=RenderStatus.SUCCESS, download_url=s3_download_url, cached=True
            )

        is_locked = await self.redis_client.set(lock_key, "locked", nx=True, ex=60)

        if not is_locked:
            return GameRenderResponse(status=RenderStatus.PENDING, cached=False)

        try:
            await self.redis_client.set(cache_key, "PENDING", ex=300)

            task = generate_game_gif.delay(
                seed=request_data.seed,
                commands=request_data.commands,
                hash_key=hash_key,
                user_id=user_id,
            )

            owner_key = RedisKeyManager.task_owner(task.id)
            await self.redis_client.set(owner_key, str(user_id), ex=3600)

            return GameRenderResponse(
                task_id=task.id, status=RenderStatus.PENDING, cached=False
            )

        finally:
            await self.redis_client.delete(lock_key)

    @staticmethod
    def create_new_game(seed: int) -> GameInfoResponse:
        game = SnakeGame()

        return GameInfoResponse(
            seed=seed,
            rules=GameRules(
                field_size=game.SIZE,
                max_commands=50,
                opposite_directions=game.OPPOSITE,
            ),
            initial_state=GameInitialState(
                snake_body=[list(cell) for cell in game.snake],
                current_direction=game.direction,
                food_position=list(game.food) if game.food else [],
            ),
        )

    async def get_status_task(self, task_id: str, user_id: UUID) -> TaskStatusResponse:
        async_result = AsyncResult(task_id)
        cache_key = f"game:task:owner:{task_id}"
        task_owner_id = await self.redis_client.get(cache_key)

        if not task_owner_id or task_owner_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой задаче или она устарела.",
            )

        state = async_result.state
        progress = 0
        result_data = None

        if state == "PROGRESS" or state == "PROCESSING":
            progress = async_result.info.get("progress", 0) if async_result.info else 0
        elif state == "SUCCESS":
            progress = 100
            result_data = async_result.result
        elif state == "FAILURE":
            result_data = {"error": str(async_result.result)}

        return TaskStatusResponse(
            task_id=task_id, status=state, progress=progress, result_data=result_data
        )
