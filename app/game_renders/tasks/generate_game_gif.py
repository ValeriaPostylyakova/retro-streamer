import io
import logging
import random
from uuid import UUID

import imageio
from celery.exceptions import Ignore

from app.core.celery_app import celery_app
from app.core.database import get_sync_session
from app.core.redis_client import get_sync_redis_client
from app.core.s3_client import get_s3_sync_client
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.models import GameRender
from app.game_renders.utils.render_board_to_image import render_board_to_image
from app.leaderboard.models import Leaderboard

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="generate_game_gif",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def generate_game_gif(
    self, seed: int, commands: list, cache_key: str, user_id: UUID
) -> str:
    random.seed(seed)
    game = SnakeGame()
    frames = []

    initial_board = game._get_board()
    frames.append(render_board_to_image(initial_board))

    for command in commands:
        try:
            board = game.step(command.lower())
            frames.append(render_board_to_image(board))
            if game.game_over:
                break
        except ValueError as e:
            logger.error(f"Invalid game command during task {self.request.id}: {e}")
            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise Ignore()

    if not frames:
        logger.warning(f"No frames generated for task {self.request.id}")
        return ""

    with io.BytesIO() as gif_io:
        imageio.mimsave(gif_io, frames, format="GIF", fps=5, loop=0)
        gif_bytes = gif_io.getvalue()

    object_name = f"games/{cache_key}.gif"

    s3_client = get_s3_sync_client()
    redis_client = get_sync_redis_client()

    s3_client.upload_file_bytes(
        file_bytes=gif_bytes, object_name=object_name, is_public=False
    )
    redis_client.set(cache_key, object_name, ex=86400)

    commands_hash = cache_key.split(":")[-1]
    scope = game.score

    with get_sync_session() as session:
        new_render = GameRender(
            user_id=user_id,
            game_name="snake",
            seed=seed,
            season_id=1,
            commands_hash=commands_hash,
            s3_key=object_name,
        )

        session.add(new_render)

        session.flush()

        new_leaderbord = Leaderboard(
            user_id=user_id,
            game_name="snake",
            scope=int(scope),
            render_id=new_render.id,
        )

        session.add(new_leaderbord)
        session.commit()

        logger.info(
            f"Game render and high score saved to database. "
            f"Render: {object_name}, Score: {scope}"
        )

    return object_name
