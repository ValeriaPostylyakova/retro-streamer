from fastapi import APIRouter, Depends, Query, status

from app.leaderboard.dependencies import get_leaderboard_service
from app.leaderboard.schemas import LeaderboardResponse
from app.leaderboard.services import LeaderboardService
from app.schemas.common import LimitOffsetResponse

router = APIRouter()


@router.get(
    "/{game_name}",
    response_model=LimitOffsetResponse[LeaderboardResponse],
    status_code=status.HTTP_200_OK,
    summary="Получение топа лидерборда для игры",
)
async def get_top_leaderboard(
    game_name: str,
    season_id: int = Query(..., description="ID текущего сезона"),
    seed: int = Query(..., description="Сид генерации уровня"),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
    limit: int = Query(
        default=20, ge=1, le=100, description="Количество возвращаемых объектов"
    ),
    offset: int = Query(
        default=0, ge=0, description="Сколько объектов пропустить с начала"
    ),
):
    return await leaderboard_service.get_leaderboard(
        game_name, season_id, seed, limit, offset
    )
