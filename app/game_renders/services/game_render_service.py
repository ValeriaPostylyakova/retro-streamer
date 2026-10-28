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
from app.game_renders.games.game_2048 import Game2048
from app.game_renders.games.labyrinth_game import LabyrinthGame
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.games.sokoban_game import SokobanGame
from app.game_renders.repositories import GameRenderRepository
from app.game_renders.schemas import (
    Game2048InfoResponse,
    Game2048InitialState,
    Game2048Rules,
    GameInfoUnion,
    GameRenderResponse,
    GameRenderResponseCache,
    GameRenderResultDTO,
    GameRequestUnion,
    LabyrinthInfoResponse,
    LabyrinthInitialState,
    LabyrinthRules,
    RenderStatus,
    SnakeInfoResponse,
    SnakeInitialState,
    SnakeRules,
    SokobanInfoResponse,
    SokobanInitialState,
    SokobanRules,
    TaskStatusResponse,
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
        request_data: GameRequestUnion,
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{request_data.game_name}:{request_data.seed}:{commands_str}:{settings.CURRENT_SEASON_ID}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(self, user_id: UUID, request_data: GameRequestUnion):
        hash_key = self._generate_idempotency_hash(request_data)
        key = RedisKeyManager.game_cache(hash_key)

        cached_data_raw = await self.redis_client.get(key)

        if cached_data_raw:
            cache_data = json.loads(cached_data_raw)

            leaderboard_dto = LeaderboardCreateDTO(
                user_id=user_id,
                render_id=UUID(cache_data["render_id"]),
                score=cache_data["score"],
                steps_count=cache_data["steps_count"],
                game_name=request_data.game_name,
                seed=request_data.seed,
            )

            await self.leaderboard_service.save_leaderboard_record(leaderboard_dto)

            return GameRenderResponseCache(
                download_url=cache_data["download_url"],
                score=cache_data["score"],
                steps_count=cache_data["steps_count"],
                render_id=UUID(cache_data["render_id"]),
            )

        db_record = await self.repository.get_render_by_commands_hash(
            commands_hash=hash_key
        )
        if db_record:
            s3_download_url = await self.s3_client.get_file_url(
                db_record.s3_key, is_public=False
            )

            cache_data = GameRenderResultDTO(
                render_id=db_record.id,
                score=db_record.score,
                steps_count=db_record.steps_count,
                download_url=s3_download_url,
            )

            await self.redis_client.set(
                key, json.dumps(cache_data.model_dump_json()), ex=86400
            )

            leaderboard_dto = LeaderboardCreateDTO(
                user_id=user_id,
                render_id=db_record.id,
                score=db_record.score,
                steps_count=db_record.steps_count,
                game_name=request_data.game_name,
                seed=request_data.seed,
            )

            await self.leaderboard_service.save_leaderboard_record(dto=leaderboard_dto)

            return GameRenderResponseCache(
                download_url=s3_download_url,
                score=db_record.score,
                steps_count=db_record.steps_count,
                render_id=db_record.id,
            )

        lock_key = RedisKeyManager.game_render_lock(hash_key)
        is_locked = await self.redis_client.set(lock_key, "processing", nx=True, ex=300)

        if not is_locked:
            raise ApplicationError(
                detail="Данный рендеринг уже находится в процессе. Пожалуйста, подождите.",
                status_code=429,
            )

        task = generate_game_gif.delay(
            game_name=request_data.game_name,
            seed=request_data.seed,
            commands=request_data.commands,
            hash_key=hash_key,
            user_id=user_id,
            lock_key=lock_key,
        )

        owner_key = RedisKeyManager.task_owner(task.id)
        await self.redis_client.set(owner_key, str(user_id), ex=300)

        return GameRenderResponse(task_id=task.id, status=RenderStatus.PENDING)

    @staticmethod
    def get_game_info(game_name: str, seed: int) -> GameInfoUnion:
        random.seed(seed)

        match game_name:
            case "snake":
                game = SnakeGame()
                return SnakeInfoResponse(
                    seed=seed,
                    rules=SnakeRules(
                        field_size=game.SIZE,
                        max_commands=250,
                        opposite_directions=game.OPPOSITE,
                        available_commands=list(game.DIRECTIONS.keys()),
                    ),
                    initial_state=SnakeInitialState(
                        snake_body=[list(cell) for cell in game.snake],
                        current_direction=game.direction,
                        food_position=list(game.food) if game.food else [],
                    ),
                )

            case "sokoban":
                game = SokobanGame()
                return SokobanInfoResponse(
                    seed=seed,
                    rules=SokobanRules(
                        field_size=game.SIZE,
                        max_commands=150,
                        available_commands=list(game.DIRECTIONS.keys()),
                    ),
                    initial_state=SokobanInitialState(
                        board=game._get_board(),
                        player_position=list(game.player),
                        boxes_positions=[list(b) for b in game.boxes],
                        targets_positions=[list(t) for t in game.targets],
                    ),
                )

            case "2048":
                game = Game2048()
                return Game2048InfoResponse(
                    seed=seed,
                    rules=Game2048Rules(
                        field_size=game.SIZE,
                        max_commands=500,
                        available_commands=list(game.DIRECTIONS.keys()),
                    ),
                    initial_state=Game2048InitialState(
                        board=game._get_board(),
                    ),
                )

            case "labyrinth":
                game = LabyrinthGame()
                return LabyrinthInfoResponse(
                    seed=seed,
                    rules=LabyrinthRules(
                        field_size=game.SIZE,
                        max_commands=150,
                        available_commands=list(game.DIRECTIONS.keys()),
                    ),
                    initial_state=LabyrinthInitialState(
                        board=game._get_board(),
                        player_position=list(game.player),
                        enemies_positions=[list(e) for e in game.enemies],
                        coins_positions=[list(c) for c in game.coins],
                    ),
                )

            case _:
                raise ValueError(f"Неизвестная игра: {game_name}")

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
                steps_count=raw_result["steps_count"],
                download_url=raw_result["download_url"],
            )
        elif state == RenderStatus.FAILED:
            task_error = async_result.result
            error_message = (
                str(task_error)
                if task_error
                else f"Задача {task_id} завершилась с ошибкой"
            )

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
