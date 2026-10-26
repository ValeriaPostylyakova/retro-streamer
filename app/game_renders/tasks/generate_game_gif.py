import logging
import random
from uuid import UUID

from celery.exceptions import Ignore

from app.core.celery_app import celery_app
from app.core.redis_client import get_sync_redis_client
from app.core.s3_client import get_s3_sync_client
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.factory import GameEngineFactory
from app.game_renders.repositories import GameRenderRepository
from app.game_renders.schemas import GameRenderResultDTO, RenderStatus
from app.game_renders.utils import create_gif_bytes
from app.game_renders.utils.send_progress_task import send_progress

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="generate_game_gif",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def generate_game_gif(
    self, game_name: str, seed: int, commands: list, hash_key: str, user_id: UUID
):
    random.seed(seed)
    task_id = self.request.id
    channel_name = RedisKeyManager.game_render_progress(task_id)
    cache_key = RedisKeyManager.game_cache(hash_key)
    redis_client = get_sync_redis_client()

    try:
        engine = GameEngineFactory.get_engine(game_name, seed)
    except ValueError as e:
        send_progress(
            task_id, channel_name=channel_name, status=RenderStatus.FAILED, error=str(e)
        )
        raise

    send_progress(
        task_id,
        channel_name,
        RenderStatus.PROCESSING,
        current_step=0,
        total_steps=len(commands),
    )

    frames = engine.get_initial_frames()
    total_commands = len(commands)

    for idx, command in enumerate(commands, start=1):
        try:
            engine.step(command)
            frames.append(engine.render_current_frame())

            send_progress(
                task_id,
                channel_name,
                RenderStatus.PROCESSING,
                current_step=idx,
                total_steps=total_commands,
            )

            if engine.game_over:
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

    frames.extend(engine.get_final_frames())

    try:
        object_name = f"games/{game_name}/{hash_key}.gif"
        gif_bytes = create_gif_bytes(frames, fps=5)

        s3_client = get_s3_sync_client()
        s3_client.upload_file_bytes(
            file_bytes=gif_bytes, object_name=object_name, is_public=False
        )
        download_url = s3_client.get_file_url(object_name, is_public=False)

        render_id = GameRenderRepository.save_game_results_to_sync_db(
            user_id=user_id,
            game_name=game_name,
            seed=seed,
            score=engine.score,
            steps_count=engine.steps_count,
            hash_key=hash_key,
            object_name=object_name,
        )

        result = GameRenderResultDTO(
            render_id=render_id,
            score=engine.score,
            steps_count=engine.steps_count,
            download_url=download_url,
        )
        redis_client.set(cache_key, result.model_dump_json(), ex=86400)

        logger.info(
            f"[{game_name.upper()}] Render saved. Score: {engine.score}, Steps: {engine.steps_count}"
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
        raise e
