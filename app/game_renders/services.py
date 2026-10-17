import hashlib
from uuid import UUID

from redis.asyncio import Redis

from app.core.s3_client import S3AsyncService
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.schemas import (
    GameInfoResponse,
    GameInitialState,
    GameRenderRequest,
    GameRenderResponse,
    GameRules,
    RenderStatus,
)
from app.game_renders.tasks.generate_game_gif import generate_game_gif


class GameRenderService:
    def __init__(self, redis_client: Redis, s3_client: S3AsyncService):
        self.redis_client = redis_client
        self.s3_client = s3_client

    def _generate_idempotency_hash(
        self,
        user_id: UUID,
        request_data: GameRenderRequest,
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{user_id}:{request_data.seed}:{commands_str}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(
        self,
        user_id: UUID,
        request_data: GameRenderRequest,
    ) -> GameRenderResponse:

        hash_key = self._generate_idempotency_hash(user_id, request_data)
        cache_key = f"game:gif:cache:{hash_key}"
        cached_file_id = await self.redis_client.get(cache_key)

        if cached_file_id:
            s3_download_url = await self.s3_client.get_file_url(
                cached_file_id, is_public=False
            )

            return GameRenderResponse(
                status=RenderStatus.SUCCESS,
                download_url=s3_download_url,
                cached=True,
            )

        task = generate_game_gif.delay(
            seed=request_data.seed,
            commands=request_data.commands,
            cache_key=cache_key,
        )

        await self.redis_client.set(f"game:task:owner:{task.id}", str(user_id), ex=3600)

        return GameRenderResponse(
            task_id=task.id, status=RenderStatus.PENDING, cached=False
        )

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
