import pytest

from app.core.exceptions import ApplicationError
from app.game_renders.schemas import TaskStatusResponse


@pytest.mark.asyncio
async def test_get_own_task_status_returns_200(client, user, render_service):
    render_service.get_status_task.return_value = TaskStatusResponse(
        task_id="task-123",
        status="PROCESSING",
        progress=50,
    )

    response = await client.get("/api/v1/game/tasks/task-123")

    assert response.status_code == 200
    assert response.json()["task_id"] == "task-123"
    assert response.json()["status"] == "PROCESSING"
    assert response.json()["progress"] == 50

    render_service.get_status_task.assert_awaited_once_with(
        "task-123",
        user.id,
    )


@pytest.mark.asyncio
async def test_get_foreign_task_status_returns_404(client, user, render_service):
    render_service.get_status_task.side_effect = ApplicationError(
        detail="Задача не найдена или у вас нет к ней доступа.",
        status_code=404,
    )

    response = await client.get("/api/v1/game/tasks/foreign-task")

    assert response.status_code == 404
    assert response.json()["detail"]

    render_service.get_status_task.assert_awaited_once_with(
        "foreign-task",
        user.id,
    )


@pytest.mark.asyncio
async def test_failed_task_status_contains_error_message(client, render_service):
    render_service.get_status_task.return_value = TaskStatusResponse(
        task_id="failed-task",
        status="FAILED",
        error="GIF upload failed",
    )

    response = await client.get("/api/v1/game/tasks/failed-task")

    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"
    assert response.json()["error"] == "GIF upload failed"
    assert response.json()["error"] != "None"
