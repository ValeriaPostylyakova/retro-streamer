from unittest.mock import MagicMock, patch  # Добавили импорт call
from uuid import uuid4

import pytest
from celery.exceptions import Ignore

from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.schemas import RenderStatus
from app.game_renders.tasks.generate_game_gif import generate_game_gif


def test_invalid_command_clears_cache_and_marks_task_failed():
    task_id = "task-invalid-command"
    hash_key = "hash-invalid-command"
    error_message = "Invalid game command"

    redis = MagicMock()

    engine = MagicMock()
    engine.get_initial_frames.return_value = []
    engine.step.side_effect = ValueError(error_message)

    cache_key = RedisKeyManager.game_cache(hash_key)
    channel_name = RedisKeyManager.game_render_progress(task_id)

    with (
        patch(
            "app.game_renders.tasks.generate_game_gif.get_sync_redis_client",
            return_value=redis,
        ),
        patch(
            "app.game_renders.tasks.generate_game_gif.GameEngineFactory.get_engine",
            return_value=engine,
        ),
        patch(
            "app.game_renders.tasks.generate_game_gif.send_progress"
        ) as send_progress,
        patch.object(generate_game_gif, "update_state") as update_state,
    ):
        generate_game_gif.push_request(id=task_id)

        with pytest.raises(Ignore):
            generate_game_gif.run(
                game_name="snake",
                seed=42,
                commands=["invalid-command"],
                hash_key=hash_key,
                user_id=uuid4(),
                lock_key=RedisKeyManager.game_render_lock("fake-hash"),
            )

    redis.delete.assert_called_once_with(cache_key)

    update_state.assert_called_once_with(
        state="FAILURE",
        meta={"error": error_message},
    )

    failed_calls = [
        c
        for c in send_progress.call_args_list
        if c.kwargs.get("status") == RenderStatus.FAILED
        or (len(c.args) >= 3 and c.args[2] == RenderStatus.FAILED)
    ]

    assert failed_calls, "Не отправлено обновление статуса FAILED"

    failed_call = failed_calls[-1]
    assert failed_call.kwargs.get("error") == error_message

    engine.step.assert_called_once_with("invalid-command")
