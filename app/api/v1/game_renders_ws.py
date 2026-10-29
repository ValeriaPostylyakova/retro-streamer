from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status

from app.auth.dependencies import get_current_user_ws
from app.game_renders.dependencies import get_game_render_websocket_service
from app.game_renders.services.websocket_service import GameRenderWebSocketService

router = APIRouter()


@router.get(
    "/stream/{task_id}",
    summary="[WebSocket] Подключение к потоку статуса задачи",
    description=(
        "### ⚠️ Внимание: это WebSocket-эндпоинт!\n\n"
        "Интерфейс Swagger UI не поддерживает интерактивное тестирование WebSocket протокола. "
        "Не нажимайте кнопку **Execute** для этого метода.\n\n"
        "**Как подключаться:**\n"
        "* URL: `ws://localhost:8000/api/v1/game/stream/{task_id}?token={access_token}`\n\n"
    ),
    status_code=status.HTTP_101_SWITCHING_PROTOCOLS,
)
def mock_websocket_docs(
    task_id: str,
    token: str = Query(
        ..., description="Действительный access_token авторизованного пользователя"
    ),
):
    pass


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
