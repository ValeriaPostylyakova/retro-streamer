from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.schemas import RenderStatus
from app.game_renders.services.game_render_service import GameRenderService


@pytest.fixture
def service():
    return GameRenderService(
        redis_client=AsyncMock(),
        s3_client=AsyncMock(),
        repository=AsyncMock(),
        leaderboard_service=AsyncMock(),
    )


@pytest.fixture
def game_request():
    return SimpleNamespace(
        game_name="snake",
        seed=42,
        commands=["up", "left", "down"],
    )


@pytest.mark.asyncio
async def test_render_does_not_enqueue_task_if_database_has_existing_render(
    service, game_request
):
    """Если рендер уже есть в БД, повторная задача не создаётся."""
    user_id = uuid4()

    existing_render = SimpleNamespace(
        id=uuid4(),
        score=100,
        steps_count=25,
        s3_key="renders/existing.gif",
    )

    service.redis_client.get.return_value = None
    service.repository.get_render_by_commands_hash.return_value = existing_render
    service.s3_client.get_file_url.return_value = (
        "https://storage.example.com/render.gif"
    )

    with patch(
        "app.game_renders.services.game_render_service.generate_game_gif.delay"
    ) as delay_mock:
        result = await service.process_game_render(user_id, game_request)

    delay_mock.assert_not_called()

    assert result.render_id == existing_render.id
    assert result.score == 100
    assert result.steps_count == 25
    assert result.download_url == "https://storage.example.com/render.gif"

    service.leaderboard_service.save_leaderboard_record.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_error_does_not_return_success_or_enqueue_task(
    service, game_request
):
    """Ошибка Redis должна передаваться вызывающему коду."""
    service.redis_client.get.side_effect = RuntimeError("Redis unavailable")

    with (
        patch(
            "app.game_renders.services.game_render_service.generate_game_gif.delay"
        ) as delay_mock,
        pytest.raises(RuntimeError, match="Redis unavailable"),
    ):
        await service.process_game_render(uuid4(), game_request)

    delay_mock.assert_not_called()
    service.repository.get_render_by_commands_hash.assert_not_awaited()


@pytest.mark.asyncio
async def test_same_request_generates_same_idempotency_hash(service, game_request):
    """Одинаковые входные данные должны давать одинаковый ключ."""
    first_hash = service._generate_idempotency_hash(game_request)
    second_hash = service._generate_idempotency_hash(game_request)

    assert first_hash == second_hash


@pytest.mark.asyncio
async def test_different_commands_generate_different_idempotency_hash(
    service, game_request
):
    """Изменение команд должно менять ключ идемпотентности."""
    original_hash = service._generate_idempotency_hash(game_request)

    changed_request = SimpleNamespace(
        game_name=game_request.game_name,
        seed=game_request.seed,
        commands=["UP", "RIGHT"],
    )
    changed_hash = service._generate_idempotency_hash(changed_request)

    assert original_hash != changed_hash


@pytest.mark.asyncio
async def test_new_render_is_sent_to_celery_and_owner_is_saved(service, game_request):
    user_id = uuid4()
    celery_task = SimpleNamespace(id="celery-task-123")
    lock_key = lock_key = RedisKeyManager.game_render_lock("some-hash")

    service.redis_client.get.return_value = None
    service.repository.get_render_by_commands_hash.return_value = None

    with (
        patch(
            "app.game_renders.services.game_render_service.generate_game_gif.delay",
            return_value=celery_task,
        ) as delay_mock,
        patch.object(
            service,
            "_generate_idempotency_hash",
            return_value="some-hash",
        ),
    ):
        result = await service.process_game_render(user_id, game_request)

    assert result.task_id == "celery-task-123"
    assert result.status == RenderStatus.PENDING

    delay_mock.assert_called_once_with(
        game_name=game_request.game_name,
        seed=game_request.seed,
        commands=game_request.commands,
        hash_key="some-hash",
        user_id=user_id,
        lock_key=lock_key,
    )

    service.redis_client.set.assert_any_await(
        RedisKeyManager.task_owner("celery-task-123"),
        str(user_id),
        ex=300,
    )
