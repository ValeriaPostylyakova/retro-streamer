import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.services import GameRenderService


@pytest.mark.asyncio
async def test_concurrent_identical_requests_only_start_one_task():
    """Два одновременных запроса: только один получает lock и запускает Celery."""
    user_id = uuid4()

    request_data = MagicMock()
    request_data.game_name = "snake"
    request_data.seed = 42
    request_data.commands = ["up", "left"]

    redis = AsyncMock()
    redis.get.return_value = None

    lock_acquired = asyncio.Event()
    set_calls = 0

    async def fake_set(key, value, **kwargs):
        nonlocal set_calls

        if kwargs.get("nx") is True:
            set_calls += 1

            if not lock_acquired.is_set():
                lock_acquired.set()
                return True

            return None

        return True

    redis.set.side_effect = fake_set

    repository = AsyncMock()
    repository.get_render_by_commands_hash.return_value = None

    s3_client = AsyncMock()
    leaderboard_service = AsyncMock()

    service = GameRenderService(
        redis_client=redis,
        repository=repository,
        s3_client=s3_client,
        leaderboard_service=leaderboard_service,
    )

    from app.game_renders import services as service_module

    fake_task = MagicMock()
    fake_task.id = "task-123"
    service_module.generate_game_gif.delay = MagicMock(return_value=fake_task)

    async def invoke():
        try:
            return await service.process_game_render(user_id, request_data)
        except Exception as exc:
            return exc

    first, second = await asyncio.gather(invoke(), invoke())

    results = [first, second]
    successes = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1

    assert getattr(failures[0], "status_code", None) == 429

    service_module.generate_game_gif.delay.assert_called_once()
    assert set_calls == 2

    redis.set.assert_any_await(
        RedisKeyManager.task_owner("task-123"),
        str(user_id),
        ex=300,
    )
