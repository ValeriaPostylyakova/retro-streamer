import asyncio
import io
import random
from uuid import UUID

import imageio
from fastapi import HTTPException

from app.core.celery_app import celery_app
from app.core.minio_client import s3_service
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.utils.render_board_to_image import render_board_to_image


@celery_app.task(bind=True, name="generate_game_gif")
def generate_game_gif(self, user_id: UUID, seed: int, commands: list, cache_key: str):
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
            raise HTTPException(status_code=400, detail=str(e))

    gif_io = io.BytesIO()

    imageio.mimsave(gif_io, frames, format="GIF", fps=5, loop=0)
    gif_io.seek(0)

    gif_bytes = gif_io.getvalue()

    object_name = f"games/{user_id}/{cache_key}.gif"
    asyncio.run(s3_service.upload_file(file_bytes=gif_bytes, object_name=object_name))
    return object_name
