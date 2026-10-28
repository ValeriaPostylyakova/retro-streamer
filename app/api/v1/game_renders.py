from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import RedirectResponse

from app.auth.dependencies import CurrentUser
from app.dependencies.rate_limiter import role_rate_limiter
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.schemas import (
    AllowedGames,
    GameInfoResponse,
    RenderRequest,
    TaskStatusResponse,
)
from app.game_renders.services import GameRenderService

router = APIRouter()


@router.get(
    "/info/{game_name}",
    summary="Получение информации о начальном положении выбранной игры",
    description="Возвращает метаданные, правила и начальное состояние выбранной игры в зависимости от seed.",
    status_code=status.HTTP_200_OK,
    response_model=GameInfoResponse,
)
async def get_game_info_dynamic(
    current_user: CurrentUser,
    game_name: AllowedGames = Path(..., description="Идентификатор игры"),
    seed: int = Query(..., description="Сид для фиксации случайного генератора"),
    service: GameRenderService = Depends(get_game_render_service),
):
    return service.get_game_info(game_name, seed)


@router.post("/render", summary="Запуск рендеринга любой игры")
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
    summary="Получение статуса генерации прохождения игры",
    response_model=TaskStatusResponse,
)
async def get_task_status(
    current_user: CurrentUser,
    task_id: str,
    service: GameRenderService = Depends(get_game_render_service),
):

    return await service.get_status_task(task_id, current_user.id)


@router.get(
    "/download/{render_id}",
    summary="Получение готового медиа файла",
    description="Генерирует безопасную временную ссылку и перенаправляет пользователя напрямую в S3/MinIO.",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def download_game_render_file(
    render_id: UUID,
    current_user: CurrentUser,
    service: GameRenderService = Depends(get_game_render_service),
):
    return await service.download_file(render_id, current_user.id)
