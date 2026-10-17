from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import CurrentUser
from app.dependencies.rate_limiter import role_rate_limiter
from app.game_renders.dependencies import get_game_render_service
from app.game_renders.schemas import (
    GameInfoResponse,
    GameRenderRequest,
    GameRenderResponse,
)
from app.game_renders.services import GameRenderService

router = APIRouter()


@router.post("/render", response_model=GameRenderResponse)
async def play_game_and_get_gif(
    current_user: CurrentUser,
    request_data: GameRenderRequest,
    _=Depends(role_rate_limiter()),
    service: GameRenderService = Depends(get_game_render_service),
):

    return await service.process_game_render(current_user.id, request_data)


@router.get("/info", response_model=GameInfoResponse)
async def get_game_info(
    service: GameRenderService = Depends(get_game_render_service),
    seed: int = Query(42, description="Сид для фиксации случайного генератора еды"),
):

    return service.create_new_game(seed)
