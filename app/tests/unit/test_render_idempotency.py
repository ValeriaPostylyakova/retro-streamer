import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.game_renders.schemas import GameRenderResponseCache
from app.game_renders.services.game_render_service import GameRenderService


@pytest.fixture
def service():
    redis = MagicMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()

    s3 = MagicMock()
    s3.get_file_url = AsyncMock()

    repository = MagicMock()
    repository.get_render_by_commands_hash = AsyncMock()

    leaderboard = MagicMock()
    leaderboard.save_leaderboard_record = AsyncMock()

    return GameRenderService(
        redis_client=redis,
        s3_client=s3,
        repository=repository,
        leaderboard_service=leaderboard,
    )


@pytest.mark.asyncio
async def test_cached_render_does_not_enqueue_new_task(service, monkeypatch):
    user_id = uuid4()
    render_id = uuid4()

    cached = {
        "render_id": str(render_id),
        "score": 120,
        "steps_count": 35,
        "download_url": "https://example.test/render.gif",
    }

    service.redis_client.get.return_value = json.dumps(cached)

    request = SimpleNamespace(
        game_name="snake",
        seed=42,
        commands=["UP", "LEFT"],
    )

    delay = MagicMock()
    monkeypatch.setattr(
        "app.game_renders.services.game_render_service.generate_game_gif.delay",
        delay,
    )

    response = await service.process_game_render(user_id, request)

    assert isinstance(response, GameRenderResponseCache)
    assert response.render_id == render_id
    assert response.score == 120
    assert response.steps_count == 35
    assert response.download_url == cached["download_url"]

    delay.assert_not_called()
    service.repository.get_render_by_commands_hash.assert_not_awaited()
    service.leaderboard_service.save_leaderboard_record.assert_awaited_once()


@pytest.mark.asyncio
async def test_existing_database_render_is_reused_without_new_task(
    service, monkeypatch
):
    user_id = uuid4()
    render_id = uuid4()
    hash_key = "existing-hash"

    service.redis_client.get.return_value = None

    db_record = SimpleNamespace(
        id=render_id,
        score=80,
        steps_count=20,
        s3_key="games/snake/existing-hash.gif",
    )
    service.repository.get_render_by_commands_hash.return_value = db_record
    service.s3_client.get_file_url.return_value = "https://example.test/existing.gif"

    request = SimpleNamespace(
        game_name="snake",
        seed=7,
        commands=["UP"],
    )

    monkeypatch.setattr(
        service,
        "_generate_idempotency_hash",
        lambda request_data: hash_key,
    )

    delay = MagicMock()
    monkeypatch.setattr(
        "app.game_renders.services.game_render_service.generate_game_gif.delay",
        delay,
    )

    response = await service.process_game_render(user_id, request)

    assert isinstance(response, GameRenderResponseCache)
    assert response.render_id == render_id
    assert response.score == 80
    assert response.steps_count == 20

    service.s3_client.get_file_url.assert_awaited_once_with(
        db_record.s3_key,
        is_public=False,
    )
    service.redis_client.set.assert_awaited_once()
    service.leaderboard_service.save_leaderboard_record.assert_awaited_once()
    delay.assert_not_called()
