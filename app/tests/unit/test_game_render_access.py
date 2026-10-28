from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ApplicationError
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.services.game_render_service import GameRenderService


@pytest.fixture
def service():
    """Создаёт сервис с изолированными зависимостями."""
    redis = AsyncMock()
    s3 = AsyncMock()
    repository = AsyncMock()
    leaderboard = AsyncMock()

    return GameRenderService(
        redis_client=redis,
        s3_client=s3,
        repository=repository,
        leaderboard_service=leaderboard,
    )


@pytest.mark.asyncio
async def test_task_status_rejects_another_users_task(service):
    """Пользователь не должен видеть чужую задачу."""
    task_id = "task-123"
    user_id = uuid4()
    another_user_id = uuid4()

    service.redis_client.get.return_value = str(another_user_id)

    with pytest.raises(ApplicationError) as exc_info:
        await service.get_status_task(task_id, user_id)

    assert exc_info.value.status_code == 404
    service.redis_client.get.assert_awaited_once_with(
        RedisKeyManager.task_owner(task_id)
    )


@pytest.mark.asyncio
async def test_task_status_rejects_task_without_owner(service):
    """Задача без записи владельца не должна быть доступна."""
    task_id = "task-without-owner"

    service.redis_client.get.return_value = None

    with pytest.raises(ApplicationError) as exc_info:
        await service.get_status_task(task_id, uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_task_status_returns_pending_for_owner(service):
    """Владелец может получить статус своей ожидающей задачи."""
    task_id = "task-pending"
    user_id = uuid4()

    service.redis_client.get.return_value = str(user_id)

    celery_result = MagicMock()
    celery_result.state = "PENDING"

    with patch(
        "app.game_renders.services.game_render_service.AsyncResult",
        return_value=celery_result,
    ):
        result = await service.get_status_task(task_id, user_id)

    assert result.task_id == task_id
    assert result.status == "PENDING"
    assert result.result is None
    assert result.error is None


@pytest.mark.asyncio
async def test_download_rejects_render_not_owned_by_user(service):
    """Нельзя скачать рендер, отсутствующий в таблице результатов пользователя."""
    render_id = uuid4()
    user_id = uuid4()

    service.leaderboard_service.get_user_render_leaderboard.return_value = None

    with pytest.raises(ApplicationError) as exc_info:
        await service.download_file(render_id, user_id)

    assert exc_info.value.status_code == 404
    service.repository.get_render_by_id.assert_not_awaited()
    service.s3_client.get_file_url.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_rejects_missing_render_record(service):
    """Если запись рендера отсутствует, ссылка на файл не создаётся."""
    render_id = uuid4()
    user_id = uuid4()

    service.leaderboard_service.get_user_render_leaderboard.return_value = {
        "render_id": render_id
    }
    service.repository.get_render_by_id.return_value = None

    with pytest.raises(ApplicationError) as exc_info:
        await service.download_file(render_id, user_id)

    assert exc_info.value.status_code == 404
    service.s3_client.get_file_url.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_returns_redirect_for_authorized_user(service):
    """Авторизованный пользователь получает временный URL для скачивания."""
    render_id = uuid4()
    user_id = uuid4()

    render_record = MagicMock()
    render_record.s3_key = "renders/example.gif"

    service.leaderboard_service.get_user_render_leaderboard.return_value = {
        "render_id": render_id
    }
    service.repository.get_render_by_id.return_value = render_record
    service.s3_client.get_file_url.return_value = (
        "https://storage.example.com/signed-render-url"
    )

    response = await service.download_file(render_id, user_id)

    assert response.status_code == 307
    assert response.headers["location"] == (
        "https://storage.example.com/signed-render-url"
    )

    service.leaderboard_service.get_user_render_leaderboard.assert_awaited_once_with(
        user_id, render_id
    )
    service.s3_client.get_file_url.assert_awaited_once_with(
        object_name="renders/example.gif",
        is_public=False,
    )
