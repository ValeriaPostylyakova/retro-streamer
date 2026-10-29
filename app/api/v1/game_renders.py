from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import RedirectResponse

from app.api.openapi_docs import (
    EXAMPLE_DOWNLOAD_URL,
    EXAMPLE_RENDER_ID,
    EXAMPLE_TASK_ID,
    GAME_INFO_EXAMPLES,
    UNAUTHORIZED_BEARER,
    detail_error,
    ok_examples,
)
from app.auth.dependencies import CurrentUser
from app.dependencies.rate_limiter import role_rate_limiter
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.schemas import AllowedGames, GameInfoResponse, RenderRequest
from app.game_renders.schemas.game_render import TaskStatusResponse
from app.game_renders.services import GameRenderService

router = APIRouter()


@router.get(
    "/info/{game_name}",
    summary="Правила и начальное состояние игры",
    description=(
        "Возвращает детерминированные правила и начальное состояние поля для выбранной игры на основе `seed`."
    ),
    status_code=status.HTTP_200_OK,
    response_model=GameInfoResponse,
    responses={
        200: ok_examples("Правила и начальное состояние игры.", GAME_INFO_EXAMPLES),
        401: UNAUTHORIZED_BEARER,
    },
)
async def get_game_info_dynamic(
    current_user: CurrentUser,
    game_name: AllowedGames = Path(
        ..., description="Идентификатор игры.", examples=["snake"]
    ),
    seed: int = Query(
        ..., description="Сид для генератора случайных чисел.", examples=[42]
    ),
    service: GameRenderService = Depends(get_game_render_service),
):
    return service.get_game_info(game_name, seed)


@router.post(
    "/render",
    summary="Запуск генерации GIF-прохождения",
    description=(
        "Принимает шаги игрока. Возвращает `status: SUCCESS` со ссылкой на готовый GIF, "
        "если аналогичный рендер уже выполнялся. В противном случае создает фоновую задачу (`status: PENDING`)."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        200: ok_examples(
            "Задача принята к исполнению либо возвращен закэшированный результат.",
            {
                "queued": (
                    "Задача поставлена в очередь",
                    {"status": "PENDING", "task_id": EXAMPLE_TASK_ID},
                ),
                "ready": (
                    "Рендер уже существует",
                    {
                        "status": "SUCCESS",
                        "score": 120,
                        "steps_count": 35,
                        "render_id": EXAMPLE_RENDER_ID,
                        "download_url": EXAMPLE_DOWNLOAD_URL,
                        "expires_in": 300,
                    },
                ),
            },
        ),
        401: UNAUTHORIZED_BEARER,
    },
)
async def play_game_dynamic(
    current_user: CurrentUser,
    request_data: RenderRequest,
    _=Depends(role_rate_limiter),
    service: GameRenderService = Depends(get_game_render_service),
):

    actual_game_request = request_data.root

    return await service.process_game_render(current_user.id, actual_game_request)


@router.get(
    "/tasks/{task_id}",
    summary="Статус задачи генерации GIF",
    description=(
        "Возвращает текущее состояние фоновой задачи Celery. "
        "Доступ к задаче ограничен её создателем и кэшируется на 5 минут после её завершения."
    ),
    response_model=TaskStatusResponse,
    responses={
        200: ok_examples(
            "Текущий статус задачи.",
            {
                "pending": (
                    "Задача в очереди или выполняется",
                    {
                        "task_id": EXAMPLE_TASK_ID,
                        "status": "PENDING",
                        "progress": None,
                        "result": None,
                        "error": None,
                    },
                ),
                "success": (
                    "Задача завершена успешно",
                    {
                        "task_id": EXAMPLE_TASK_ID,
                        "status": "SUCCESS",
                        "progress": None,
                        "result": {
                            "render_id": EXAMPLE_RENDER_ID,
                            "score": 120,
                            "steps_count": 35,
                            "download_url": EXAMPLE_DOWNLOAD_URL,
                        },
                        "error": None,
                    },
                ),
                "failed": (
                    "Задача завершилась с ошибкой",
                    {
                        "task_id": EXAMPLE_TASK_ID,
                        "status": "FAILED",
                        "progress": None,
                        "result": None,
                        "error": "GIF upload failed",
                    },
                ),
            },
        ),
        401: UNAUTHORIZED_BEARER,
        404: detail_error(
            "Задача не найдена или истекло время хранения связи с владельцем.",
            {
                "not_found": (
                    "Нет доступа",
                    "Задача не найдена или у вас нет к ней доступа.",
                )
            },
        ),
    },
)
async def get_task_status(
    current_user: CurrentUser,
    task_id: str = Path(..., description="Идентификатор задачи (task_id)."),
    service: GameRenderService = Depends(get_game_render_service),
):
    return await service.get_status_task(task_id, current_user.id)


@router.get(
    "/download/{render_id}",
    summary="Скачивание готового GIF",
    description=(
        "Генерирует временную подписанную ссылку на файл в S3/MinIO и "
        "перенаправляет клиента через HTTP 307 Temporary Redirect."
    ),
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={
        307: {
            "description": "Перенаправление на временный URL скачивания в S3 (ссылка активна 5 минут).",
            "headers": {
                "Location": {
                    "description": "Предподписанный URL.",
                    "schema": {"type": "string", "example": EXAMPLE_DOWNLOAD_URL},
                }
            },
        },
        401: UNAUTHORIZED_BEARER,
        404: detail_error(
            "Рендер не найден или у пользователя нет прав на его скачивание.",
            {
                "no_access": (
                    "Нет прав",
                    "Файл не найден или у вас нет прав на его скачивание.",
                ),
                "no_record": (
                    "Не найдено в БД",
                    "Запись рендера не найдена в базе данных.",
                ),
            },
        ),
    },
)
async def download_game_render_file(
    render_id: Annotated[UUID, Path(description="Идентификатор рендера (UUID).")],
    current_user: CurrentUser,
    service: GameRenderService = Depends(get_game_render_service),
):
    return await service.download_file(render_id, current_user.id)
