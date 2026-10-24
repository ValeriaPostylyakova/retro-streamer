from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket

from app.core.security import get_current_user_ws
from app.game_renders.dependencies import get_game_render_websocket_service
from app.game_renders.services.websocket_service import GameRenderWebSocketService

router = APIRouter()


@router.websocket("/stream/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
    websocket_service: GameRenderWebSocketService = Depends(
        get_game_render_websocket_service
    ),
):
    try:
        user_id = await get_current_user_ws(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await websocket_service.stream_task_status(websocket, task_id, user_id)
