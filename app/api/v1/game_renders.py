from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from app.auth.dependencies import CurrentUser
from app.dependencies.rate_limiter import role_rate_limiter
from app.enums import AllowedSeeds
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.schemas import (
    SnakeInfoResponse,
    SnakeRenderRequest,
    TaskStatusResponse,
    TetrisInfoResponse,
    TetrisRenderRequest,
)
from app.game_renders.services import GameRenderService

router = APIRouter()


@router.get(
    "/info/snake",
    summary="Получение информации о начальном положении игры snake",
    description="Возвращает информацию о начальном положении игры в зависимости от параметра seed.",
    status_code=status.HTTP_200_OK,
    response_model=SnakeInfoResponse,
)
async def get_game_info(
    current_user: CurrentUser,
    seed: AllowedSeeds = Query(
        ..., description="Сид для фиксации случайного генератора еды"
    ),
    service: GameRenderService = Depends(get_game_render_service),
):

    return service.get_info_snake(seed.value)


@router.get(
    "/info/tetris",
    summary="Получение информации о начальном положении игры tetris",
    description="Возвращает информацию о начальном положении игры в зависимости от параметра seed.",
    status_code=status.HTTP_200_OK,
    response_model=TetrisInfoResponse,
)
async def get_tetris_game_info(
    current_user: CurrentUser,
    seed: AllowedSeeds = Query(..., description="Сид для фиксации генератора фигур"),
    service: GameRenderService = Depends(get_game_render_service),
):
    return service.get_info_tetris(seed.value)


@router.post("/render/snake", summary="Запуск игры")
async def play_game_snake(
    current_user: CurrentUser,
    request_data: SnakeRenderRequest,
    _=Depends(role_rate_limiter()),
    service: GameRenderService = Depends(get_game_render_service),
):

    return await service.process_game_render(current_user.id, request_data)


@router.post("/render/tetris", summary="Запуск игры")
async def play_game_tetris(
    current_user: CurrentUser,
    request_data: TetrisRenderRequest,
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
