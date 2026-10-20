import hashlib
import json
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
    GameRenderResponseCache,
    GameRules,
    RenderStatus,
    TaskStatusResponse,
)
from app.game_renders.tasks.generate_game_gif import generate_game_gif
from app.leaderboard.repositories import LeaderboardRepository


class GameRenderService:
    def __init__(
        self,
        redis_client: Redis,
        s3_client: S3AsyncService,
        repository: GameRenderRepository,
        leaderboard_repository: LeaderboardRepository,
    ):
        self.redis_client = redis_client
        self.s3_client = s3_client
        self.repository = repository
        self.leaderboard_repository = leaderboard_repository

    def _generate_idempotency_hash(
        self,
        request_data: GameRenderRequest,
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{request_data.seed}:{commands_str}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(self, user_id: UUID, request_data: GameRenderRequest):
        hash_key = self._generate_idempotency_hash(request_data)
        key = RedisKeyManager.game_cache(hash_key)

        cached_data_raw = await self.redis_client.get(key)

        if cached_data_raw:
            cache_data = json.loads(cached_data_raw)

            await self.leaderboard_repository.save_leaderboard_record(
                user_id=user_id,
                render_id=cache_data["render_id"],
                score=cache_data["score"],
                game_name="snake",
            )

            s3_download_url = await self.s3_client.get_file_url(
                cache_data["s3_key"], is_public=False
            )
            return GameRenderResponseCache(download_url=s3_download_url)

        db_record = await self.repository.get_render_by_commands_hash(
            commands_hash=hash_key
        )
        if db_record:
            cache_data = {
                "s3_key": db_record.s3_key,
                "render_id": str(db_record.id),
                "score": db_record.score,
            }
            await self.redis_client.set(key, json.dumps(cache_data), ex=86400)

            await self.leaderboard_repository.save_leaderboard_record(
                user_id=user_id,
                render_id=db_record.id,
                score=db_record.score,
                game_name="snake",
            )

            s3_download_url = await self.s3_client.get_file_url(
                db_record.s3_key, is_public=False
            )
            return GameRenderResponseCache(download_url=s3_download_url)

        task = generate_game_gif.delay(
            seed=request_data.seed,
            commands=request_data.commands,
            hash_key=hash_key,
            user_id=user_id,
        )

        owner_key = RedisKeyManager.task_owner(task.id)
        await self.redis_client.set(owner_key, str(user_id), ex=3600)

        return GameRenderResponse(task_id=task.id, status=RenderStatus.PENDING)

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
        cache_key = RedisKeyManager.task_owner(task_id)
        task_owner_id = await self.redis_client.get(cache_key)

        if not task_owner_id or task_owner_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этой задаче или она устарела.",
            )

        state = async_result.state
        progress = 0
        result_data = None

        if state == RenderStatus.PROGRESS or state == RenderStatus.PROCESSING:
            progress = async_result.info.get("progress", 0) if async_result.info else 0
        elif state == RenderStatus.SUCCESS:
            progress = 100
            result_data = async_result.result
        elif state == RenderStatus.FAILED:
            result_data = {"error": str(async_result.result)}

        return TaskStatusResponse(
            task_id=task_id, status=state, progress=progress, result_data=result_data
        )
