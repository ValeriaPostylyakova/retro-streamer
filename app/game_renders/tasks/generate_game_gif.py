import io
import logging
import random
import time
from uuid import UUID

import imageio
from celery.exceptions import Ignore
from sqlalchemy.dialects.postgresql import insert

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_sync_session
from app.core.redis_client import get_sync_redis_client
from app.core.s3_client import get_s3_sync_client
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.games.tetris_game import TetrisGame
from app.game_renders.models import GameRender
from app.game_renders.schemas import GameRenderResultDTO, RenderStatus
from app.game_renders.utils.render_board_to_image import render_board_to_image
from app.game_renders.utils.send_progress_task import send_progress
from app.leaderboard.models import Leaderboard

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="generate_game_gif",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def generate_game_gif(
    self,
    game_name: str,
    seed: int,
    commands: list,
    hash_key: str,
    user_id: UUID,
):
    random.seed(seed)

    task_id = self.request.id
    channel_name = RedisKeyManager.game_render_progress(task_id)
    redis_client = get_sync_redis_client()
    cache_key = RedisKeyManager.game_cache(hash_key)

    existing_cache = redis_client.get(cache_key)
    if existing_cache:
        logger.info(
            f"Task {task_id} found existing cache for hash {hash_key}. Skipping execution."
        )
        try:
            cached_dto = GameRenderResultDTO.model_validate_json(existing_cache)
            send_progress(
                task_id,
                channel_name,
                RenderStatus.SUCCESS,
                current_step=1,
                total_steps=1,
                result=cached_dto,
            )
            return cached_dto.model_dump(mode="json")
        except Exception:
            pass

    send_progress(
        task_id=task_id,
        channel_name=channel_name,
        status=RenderStatus.PROCESSING,
        current_step=0,
        total_steps=len(commands),
    )

    if game_name == "snake":
        game = SnakeGame()
    elif game_name == "tetris":
        game = TetrisGame()
    else:
        send_progress(task_id, channel_name=channel_name, status=RenderStatus.FAILED)
        raise ValueError(f"Unknown game name: {game_name}")

    frames = []
    initial_board = game._get_board()
    frames.append(render_board_to_image(initial_board, game_name=game_name))

    total_commands = len(commands)
    for idx, command in enumerate(commands, start=1):
        time.sleep(2)

        try:
            board = game.step(command.lower())
            frames.append(render_board_to_image(board, game_name=game_name))

            send_progress(
                task_id,
                channel_name,
                RenderStatus.PROCESSING,
                current_step=idx,
                total_steps=total_commands,
            )

            if game.game_over:
                send_progress(
                    task_id,
                    channel_name,
                    RenderStatus.PROCESSING,
                    current_step=total_commands,
                    total_steps=total_commands,
                )
                break
        except ValueError as e:
            logger.error(f"Invalid game command during task {task_id}: {e}")
            redis_client.delete(cache_key)
            send_progress(task_id, channel_name, RenderStatus.FAILED, error=str(e))
            self.update_state(state="FAILURE", meta={"error": str(e)})
            raise Ignore()

    if not frames:
        logger.warning(f"No frames generated for task {task_id}")
        redis_client.delete(cache_key)
        send_progress(
            task_id, channel_name, RenderStatus.FAILED, error="No frames generated"
        )
        return ""

    with io.BytesIO() as gif_io:
        imageio.mimsave(gif_io, frames, format="GIF", fps=5, loop=0)
        gif_bytes = gif_io.getvalue()

    object_name = f"games/{game_name}/{hash_key}.gif"
    s3_client = get_s3_sync_client()

    try:
        s3_client.upload_file_bytes(
            file_bytes=gif_bytes, object_name=object_name, is_public=False
        )

        download_url = s3_client.get_file_url(object_name, is_public=False)
        score = int(game.score)

        with get_sync_session() as session:
            new_render = GameRender(
                game_name=game_name,
                seed=seed,
                score=int(score),
                season_id=settings.CURRENT_SEASON_ID,
                commands_hash=hash_key,
                s3_key=object_name,
            )
            session.add(new_render)
            session.flush()

            stmt = insert(Leaderboard).values(
                user_id=user_id,
                game_name=game_name,
                score=int(score),
                render_id=new_render.id,
                season_id=settings.CURRENT_SEASON_ID,
                seed=seed,
            )

            safe_stmt = stmt.on_conflict_do_nothing(
                index_elements=["user_id", "render_id"]
            )

            session.execute(safe_stmt)
            session.commit()

            cache_data = GameRenderResultDTO(
                render_id=new_render.id,
                score=int(score),
                download_url=download_url,
            )

            redis_client.set(cache_key, cache_data.model_dump_json(), ex=86400)

            logger.info(
                f"[{game_name.upper()}] Game render and high score saved to database. "
                f"Render: {object_name}, Score: {score}"
            )

        result = GameRenderResultDTO(
            render_id=new_render.id,
            score=score,
            download_url=download_url,
        )

        send_progress(
            task_id,
            channel_name,
            RenderStatus.SUCCESS,
            current_step=1,
            total_steps=1,
            result=result,
        )

        return result.model_dump(mode="json")

    except Exception as e:
        logger.error(f"Error finalizing task {task_id}: {e}", exc_info=True)
        if self.request.retries == self.max_retries:
            logger.critical(
                f"Task {task_id} failed after max retries. Cleaning up Redis."
            )
            redis_client.delete(cache_key)
            send_progress(task_id, channel_name, RenderStatus.FAILED, error=str(e))
        return_raise = e
        raise return_raise
