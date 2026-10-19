from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from app.auth.dependencies import CurrentUser
from app.core.s3_client import s3_async_client
from app.dependencies.rate_limiter import role_rate_limiter
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.schemas import (
    GameInfoResponse,
    GameRenderRequest,
    GameRenderResponse,
    TaskStatusResponse,
)
from app.game_renders.services import GameRenderService

router = APIRouter()


@router.get(
    "/info",
    summary="Получение информации о начальном положении игры",
    description="Возвращает информацию о начальном положении игры в зависимости от параметра seed.",
    status_code=status.HTTP_200_OK,
    response_model=GameInfoResponse,
)
async def get_game_info(
    current_user: CurrentUser,
    seed: int = Query(42, description="Сид для фиксации случайного генератора еды"),
    service: GameRenderService = Depends(get_game_render_service),
):

    return service.create_new_game(seed)


@router.post("/render", summary="Запуск игры", response_model=GameRenderResponse)
async def play_game_and_get_gif(
    current_user: CurrentUser,
    request_data: GameRenderRequest,
    _=Depends(role_rate_limiter()),
    service: GameRenderService = Depends(get_game_render_service),
):

    return await service.process_game_render(current_user.id, request_data)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    current_user: CurrentUser,
    task_id: str,
    service: GameRenderService = Depends(get_game_render_service),
):

    return await service.get_status_task(task_id, current_user.id)


@router.get(
    "/download",
    summary="Получение готового медиа файла",
    description="Генерирует безопасную временную ссылку и перенаправляет пользователя напрямую в S3/MinIO.",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def download_game_render_file(s3_key: str, current_user: CurrentUser):
    presigned_url = await s3_async_client.get_file_url(
        object_name=s3_key, is_public=False
    )

    return RedirectResponse(url=presigned_url)
