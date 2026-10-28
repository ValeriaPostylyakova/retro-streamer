from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.schemas import RenderStatus
from app.game_renders.services.game_render_service import GameRenderService


@pytest.mark.asyncio
async def test_failed_task_returns_actual_error_message():
    redis = AsyncMock()
    user_id = uuid4()
    task_id = "failed-task-123"
    error_message = "MinIO is unavailable"

    redis.get.return_value = str(user_id)

    service = GameRenderService(
        redis_client=redis,
        s3_client=AsyncMock(),
        repository=AsyncMock(),
        leaderboard_service=AsyncMock(),
    )

    celery_result = MagicMock()
    celery_result.state = RenderStatus.FAILED
    celery_result.result = RuntimeError(error_message)

    with patch(
        "app.game_renders.services.game_render_service.AsyncResult",
        return_value=celery_result,
    ):
        result = await service.get_status_task(task_id, user_id)

    assert result.status == RenderStatus.FAILED
    assert result.error == error_message
    assert result.result is None

    redis.get.assert_awaited_once_with(RedisKeyManager.task_owner(task_id))
