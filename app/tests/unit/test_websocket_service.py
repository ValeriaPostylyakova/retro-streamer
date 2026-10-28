import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ApplicationError
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.schemas import RenderStatus
from app.game_renders.services.websocket_service import (
    GameRenderWebSocketService,
)


@pytest.mark.asyncio
async def test_websocket_closes_when_user_does_not_own_task():
    """Чужая задача не должна открывать WebSocket-поток."""
    websocket = MagicMock()
    websocket.close = AsyncMock()
    # ИСПРАВЛЕНИЕ: Явно объявляем accept как AsyncMock, чтобы работал assert_not_awaited
    websocket.accept = AsyncMock()

    redis = MagicMock()
    render_service = MagicMock()
    render_service.get_status_task = AsyncMock(
        side_effect=ApplicationError("Task not found", status_code=404)
    )

    service = GameRenderWebSocketService(redis, render_service)

    await service.stream_task_status(
        websocket=websocket,
        task_id="another-users-task",
        user_id=uuid4(),
    )

    websocket.close.assert_awaited_once_with(code=4404)
    websocket.accept.assert_not_awaited()
    redis.pubsub.assert_not_called()


@pytest.mark.asyncio
async def test_websocket_sends_terminal_status_and_closes_pubsub():
    """При уже завершённой задаче отправляется статус и закрывается подписка."""
    task_id = "completed-task"
    user_id = uuid4()

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()

    terminal_status = SimpleNamespace(
        task_id=task_id,
        status=RenderStatus.SUCCESS,
        model_dump=lambda mode: {
            "task_id": task_id,
            "status": "SUCCESS",
            "progress": 100,
            "result": None,
            "error": None,
        },
    )

    render_service = MagicMock()
    render_service.get_status_task = AsyncMock(return_value=terminal_status)

    pubsub = MagicMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()

    redis = MagicMock()
    redis.pubsub.return_value = pubsub

    service = GameRenderWebSocketService(redis, render_service)

    await service.stream_task_status(websocket, task_id, user_id)

    websocket.accept.assert_awaited_once()
    websocket.send_json.assert_awaited_once_with(
        terminal_status.model_dump(mode="json")
    )

    channel = RedisKeyManager.game_render_progress(task_id)
    pubsub.subscribe.assert_awaited_once_with(channel)
    pubsub.unsubscribe.assert_awaited_once_with(channel)
    pubsub.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_websocket_forwards_progress_until_task_finishes():
    """Промежуточный прогресс и финальный статус доходят до клиента."""
    task_id = "running-task"
    user_id = uuid4()

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()

    initial_status = SimpleNamespace(
        task_id=task_id,
        status=RenderStatus.PROGRESS,
        model_dump=lambda mode: {
            "task_id": task_id,
            "status": "PROGRESS",
            "progress": 20,
            "result": None,
            "error": None,
        },
    )

    render_service = MagicMock()
    render_service.get_status_task = AsyncMock(return_value=initial_status)

    progress_message = {
        "type": "message",
        "data": json.dumps({"status": "PROGRESS", "progress": 60}),
    }
    final_message = {
        "type": "message",
        "data": json.dumps({"status": "SUCCESS", "progress": 100}),
    }

    async def listen():
        yield progress_message
        yield final_message

    pubsub = MagicMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    pubsub.listen.return_value = listen()

    redis = MagicMock()
    redis.pubsub.return_value = pubsub

    service = GameRenderWebSocketService(redis, render_service)

    await service.stream_task_status(websocket, task_id, user_id)

    assert websocket.send_json.await_count == 3
    # ИСПРАВЛЕНИЕ: Переменная c используется вместо call, чтобы не путать с unittest.mock.call
    sent_messages = [c.args[0] for c in websocket.send_json.await_args_list]

    assert sent_messages[0]["status"] == "PROGRESS"
    assert sent_messages[1] == {"status": "PROGRESS", "progress": 60}
    assert sent_messages[2] == {"status": "SUCCESS", "progress": 100}

    pubsub.unsubscribe.assert_awaited_once()
    pubsub.aclose.assert_awaited_once()
