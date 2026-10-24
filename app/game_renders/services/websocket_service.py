import json
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.core.exceptions import ApplicationError
from app.game_renders.cache_keys import RedisKeyManager
from app.game_renders.schemas import RenderStatus
from app.game_renders.services import GameRenderService


class GameRenderWebSocketService:
    def __init__(self, redis_client: Redis, render_service: GameRenderService):
        self.redis_client = redis_client
        self.render_service = render_service

    async def stream_task_status(
        self, websocket: WebSocket, task_id: str, user_id: UUID
    ):
        try:
            current_status = await self.render_service.get_status_task(
                task_id=task_id, user_id=user_id
            )
        except ApplicationError as exc:
            await websocket.close(code=4404 if exc.status_code == 404 else 4400)
            return

        pubsub = self.redis_client.pubsub()
        channel_name = RedisKeyManager.game_render_progress(task_id)

        try:
            await pubsub.subscribe(channel_name)
            await websocket.accept()

            await websocket.send_json(current_status.model_dump(mode="json"))

            if current_status.status in (RenderStatus.SUCCESS, RenderStatus.FAILED):
                return

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = json.loads(message["data"])
                await websocket.send_json(data)

                if data.get("status") in (RenderStatus.SUCCESS, RenderStatus.FAILED):
                    break

        except WebSocketDisconnect:
            pass
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.aclose()
