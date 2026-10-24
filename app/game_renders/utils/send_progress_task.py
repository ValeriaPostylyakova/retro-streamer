from app.core.redis_client import get_sync_redis_client
from app.game_renders.schemas import (
    GameRenderResultDTO,
    RenderStatus,
    TaskStatusResponse,
)


def send_progress(
    task_id: str,
    channel_name: str,
    status: RenderStatus,
    current_step: int = 0,
    total_steps: int = 0,
    result: GameRenderResultDTO | None = None,
    error: str | None = None,
):
    redis_client = get_sync_redis_client()

    progress_val = int((current_step / total_steps) * 100) if total_steps > 0 else 0

    payload = TaskStatusResponse(
        task_id=task_id,
        status=status,
        progress=progress_val,
        result=result,
        error=error,
    )

    redis_client.publish(channel_name, payload.model_dump_json())
