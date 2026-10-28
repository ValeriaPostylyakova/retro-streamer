import pytest

from app.game_renders.schemas import GameRenderResponse, RenderStatus


@pytest.mark.asyncio
async def test_render_valid_request_returns_pending(client, user, render_service):
    render_service.process_game_render.return_value = GameRenderResponse(
        status=RenderStatus.PENDING,
        task_id="task-123",
    )

    response = await client.post(
        "/api/v1/game/render",
        json={
            "game_name": "snake",
            "seed": 42,
            "commands": ["up", "left"],
        },
    )

    assert response.status_code == 200
    assert response.json()["task_id"] == "task-123"
    assert response.json()["status"] == "PENDING"

    render_service.process_game_render.assert_awaited_once()
    args = render_service.process_game_render.await_args.args
    assert args[0] == user.id
    assert args[1].game_name == "snake"


@pytest.mark.asyncio
async def test_render_rejects_invalid_commands(client, render_service):
    response = await client.post(
        "/api/v1/game/render",
        json={
            "game_name": "snake",
            "seed": 42,
            "commands": ["fly", "left"],
        },
    )

    assert response.status_code == 422
    render_service.process_game_render.assert_not_awaited()


@pytest.mark.asyncio
async def test_render_rejects_unknown_game(client, render_service):
    response = await client.post(
        "/api/v1/game/render",
        json={
            "game_name": "unknown-game",
            "seed": 42,
            "commands": ["up", "left"],
        },
    )

    assert response.status_code == 422
    render_service.process_game_render.assert_not_awaited()


@pytest.mark.asyncio
async def test_render_rejects_too_few_commands(client, render_service):
    response = await client.post(
        "/api/v1/game/render",
        json={
            "game_name": "snake",
            "seed": 42,
            "commands": ["up"],
        },
    )

    assert response.status_code == 422
    render_service.process_game_render.assert_not_awaited()
