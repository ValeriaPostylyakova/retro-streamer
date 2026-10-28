from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_current_user
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.services.game_render_service import GameRenderService
from app.main import app


@pytest.mark.asyncio
async def test_render_api_uses_real_service_and_queues_task(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        email="player@example.com",
        hashed_password="test-password-hash",
        role="default",
        is_active=True,
    )

    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()

    s3 = MagicMock()
    repository = MagicMock()
    repository.get_render_by_commands_hash = AsyncMock(return_value=None)

    leaderboard = MagicMock()
    leaderboard.save_leaderboard_record = AsyncMock()

    service = GameRenderService(
        redis_client=redis,
        s3_client=s3,
        repository=repository,
        leaderboard_service=leaderboard,
    )

    queued_task = SimpleNamespace(id="integration-task-123")
    delay = MagicMock(return_value=queued_task)

    monkeypatch.setattr(
        "app.game_renders.services.game_render_service.generate_game_gif.delay",
        delay,
    )

    async def override_user():
        return user

    async def override_service():
        return service

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_game_render_service] = override_service

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/game/render",
                json={
                    "game_name": "snake",
                    "seed": 42,
                    "commands": ["up", "left"],
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["task_id"] == "integration-task-123"
        assert body["status"] == "PENDING"

        repository.get_render_by_commands_hash.assert_awaited_once()
        delay.assert_called_once()

        task_kwargs = delay.call_args.kwargs
        assert task_kwargs["game_name"] == "snake"
        assert task_kwargs["seed"] == 42
        assert task_kwargs["commands"] == ["up", "left"]
        assert task_kwargs["user_id"] == user.id

        assert redis.set.await_count >= 1
        redis_key, owner = redis.set.call_args.args[:2]
        assert owner == str(user.id)
        assert "integration-task-123" in redis_key

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_game_render_service, None)
