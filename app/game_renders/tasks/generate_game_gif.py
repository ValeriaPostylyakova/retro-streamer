import io
import logging
import random

import imageio
from celery.exceptions import Ignore

from app.core.celery_app import celery_app
from app.core.redis_client import get_sync_redis_client
from app.core.s3_client import get_s3_sync_client
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.utils.render_board_to_image import render_board_to_image

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="generate_game_gif",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def generate_game_gif(self, seed: int, commands: list, cache_key: str) -> str:
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

    return object_name
