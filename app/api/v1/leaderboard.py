from fastapi import APIRouter, Depends, Query, status

from app.leaderboard.dependencies import get_leaderboard_service
from app.leaderboard.schemas import LeaderboardResponse
from app.leaderboard.services import LeaderboardService

router = APIRouter()


@router.get(
    "/{game_name}",
    response_model=list[LeaderboardResponse],
    status_code=status.HTTP_200_OK,
    summary="Получение топа лидерборда для игры",
)
async def get_top_leaderboard(
    game_name: str,
    season_id: int = Query(..., description="ID текущего сезона"),
    seed: int = Query(..., description="Сид генерации уровня"),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    return await leaderboard_service.get_top_leaderboard(game_name, season_id, seed)
