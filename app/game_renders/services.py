import hashlib
from uuid import UUID

from app.core.redis_client import redis_client
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
    def _generate_idempotency_hash(
        self, user_id: UUID, request_data: GameRenderRequest
    ) -> str:
        commands_str = ",".join(request_data.commands)
        raw_string = f"{user_id}:{request_data.seed}:{commands_str}"
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    async def process_game_render(
        self, user_id: UUID, request_data: GameRenderRequest
    ) -> GameRenderResponse:

        hash_key = self._generate_idempotency_hash(user_id, request_data)
        cache_key = f"render_cache:{hash_key}"
        cached_file_id = await redis_client.get(cache_key)

        if cached_file_id:
            file_id_str = cached_file_id.decode("utf-8")
            return GameRenderResponse(
                status=RenderStatus.SUCCESS,
                download_url=f"/api/v1/game/download/{file_id_str}",
                cached=True,
            )

        task = generate_game_gif.delay(
            user_id=str(user_id),
            seed=request_data.seed,
            commands=request_data.commands,
            cache_key=cache_key,
        )

        await redis_client.set(f"task_owner:{task.id}", str(user_id), ex=3600)

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
