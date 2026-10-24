import hashlib
import json
import random
from uuid import UUID

from celery.result import AsyncResult
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.s3_client import S3AsyncService
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.games.tetris_game import TetrisGame
from app.game_renders.repositories import GameRenderRepository
from app.game_renders.schemas import (
    GameRenderResponse,
    GameRenderResponseCache,
    GameRenderResultDTO,
    RenderStatus,
    SnakeInfoResponse,
    SnakeInitialState,
    SnakeRenderRequest,
    SnakeRules,
    TaskStatusResponse,
    TetrisInfoResponse,
    TetrisInitialState,
    TetrisRenderRequest,
    TetrisRules,
)
from app.game_renders.tasks.generate_game_gif import generate_game_gif
from app.leaderboard.schemas import LeaderboardCreateDTO
from app.leaderboard.services import LeaderboardService


class GameRenderService:
    def __init__(
        self,
        redis_client: Redis,
        s3_client: S3AsyncService,
        repository: GameRenderRepository,
        leaderboard_service: LeaderboardService,
    ):
        self.redis_client = redis_client
        self.s3_client = s3_client
        self.repository = repository
        self.leaderboard_service = leaderboard_service

    def _generate_idempotency_hash(
        self,
        request_data,
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{request_data.seed}:{commands_str}:{settings.CURRENT_SEASON_ID}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(
        self, user_id: UUID, request_data: SnakeRenderRequest | TetrisRenderRequest
    ):
        hash_key = self._generate_idempotency_hash(request_data)
        key = RedisKeyManager.game_cache(hash_key)

        cached_data_raw = await self.redis_client.get(key)

        if cached_data_raw:
            cache_data = json.loads(cached_data_raw)

            leaderboard_dto = LeaderboardCreateDTO(
                user_id=user_id,
                render_id=UUID(cache_data["render_id"]),
                score=cache_data["score"],
                game_name=request_data.game_name,
                seed=request_data.seed,
            )

            await self.leaderboard_service.save_leaderboard_record(leaderboard_dto)

            return GameRenderResponseCache(
                download_url=cache_data["download_url"],
                score=cache_data["score"],
                render_id=UUID(cache_data["render_id"]),
            )

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

            leaderboard_dto = LeaderboardCreateDTO(
                user_id=user_id,
                render_id=UUID(cache_data["render_id"]),
                score=cache_data["score"],
                game_name=request_data.game_name,
                seed=request_data.seed,
            )

            await self.leaderboard_service.save_leaderboard_record(dto=leaderboard_dto)

            s3_download_url = await self.s3_client.get_file_url(
                db_record.s3_key, is_public=False
            )
            return GameRenderResponseCache(
                download_url=s3_download_url,
                score=cache_data["score"],
                render_id=UUID(cache_data["render_id"]),
            )

        task = generate_game_gif.delay(
            game_name=request_data.game_name,
            seed=request_data.seed,
            commands=request_data.commands,
            hash_key=hash_key,
            user_id=str(user_id),
        )

        owner_key = RedisKeyManager.task_owner(task.id)
        await self.redis_client.set(owner_key, str(user_id), ex=300)

        return GameRenderResponse(task_id=task.id, status=RenderStatus.PENDING)

    @staticmethod
    def get_info_snake(seed: int) -> SnakeInfoResponse:
        random.seed(seed)
        game = SnakeGame()

        return SnakeInfoResponse(
            seed=seed,
            rules=SnakeRules(
                field_size=game.SIZE,
                opposite_directions=game.OPPOSITE,
            ),
            initial_state=SnakeInitialState(
                snake_body=[list(cell) for cell in game.snake],
                current_direction=game.direction,
                food_position=list(game.food) if game.food else [],
            ),
        )

    @staticmethod
    def get_info_tetris(seed: int) -> TetrisInfoResponse:
        random.seed(seed)
        game = TetrisGame()

        return TetrisInfoResponse(
            seed=seed,
            rules=TetrisRules(
                field_size=(game.HEIGHT, game.WIDTH),
            ),
            initial_state=TetrisInitialState(board=game._get_board()),
        )

    async def get_status_task(self, task_id: str, user_id: UUID) -> TaskStatusResponse:
        async_result = AsyncResult(task_id)
        cache_key = RedisKeyManager.task_owner(task_id)
        task_owner_id = await self.redis_client.get(cache_key)

        if not task_owner_id or task_owner_id != str(user_id):
            raise ApplicationError(
                detail="Задача не найдена или у вас нет к ней доступа.",
                status_code=404,
            )

        state = async_result.state
        result_data = None
        error_message = None

        if state == RenderStatus.SUCCESS:
            raw_result = async_result.result
            result_data = GameRenderResultDTO(
                render_id=UUID(raw_result["render_id"]),
                score=raw_result["score"],
                download_url=raw_result["download_url"],
            )
        elif state == RenderStatus.FAILED:
            error_message = str(result_data)

        return TaskStatusResponse(
            task_id=task_id,
            status=state,
            result=result_data,
            error=error_message,
        )

    async def download_file(self, render_id: UUID, user_id: UUID) -> RedirectResponse:
        leaderboard_data = await self.leaderboard_service.get_user_render_leaderboard(
            user_id, render_id
        )

        if not leaderboard_data:
            raise ApplicationError(
                detail="Файл не найден или у вас нет прав на его скачивание.",
                status_code=404,
            )

        render_record = await self.repository.get_render_by_id(render_id)

        if not render_record:
            raise ApplicationError(
                detail="Запись рендера не найдена в базе данных.",
                status_code=404,
            )

        presigned_url = await self.s3_client.get_file_url(
            object_name=render_record.s3_key, is_public=False
        )

        return RedirectResponse(url=presigned_url)
