from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.openapi_docs import (
    UNAUTHORIZED_BEARER,
    ok_examples,
)
from app.auth.dependencies import CurrentUser
from app.game_renders.schemas import AllowedGames
from app.leaderboard.dependencies import get_leaderboard_service
from app.leaderboard.schemas import LeaderboardResponse
from app.leaderboard.services import LeaderboardService
from app.schemas.common import LimitOffsetResponse

router = APIRouter()


@router.get(
    "/{game_name}",
    response_model=LimitOffsetResponse[LeaderboardResponse],
    status_code=status.HTTP_200_OK,
    summary="Топ игроков по игре, сезону и seed",
    description="Возвращает пагинированную страницу таблицы лидеров с лучшими результатами пользователей.",
    responses={
        200: ok_examples(
            "Страница таблицы лидеров.",
            {
                "page": (
                    "Пример страницы с результатами",
                    {
                        "items": [
                            {
                                "id": 17,
                                "game_name": "snake",
                                "score": 120,
                                "steps_count": 35,
                                "created_at": "2026-10-28T09:15:42.123456",
                                "user": {
                                    "id": "3f2b8c1e-7a4d-4e1b-9c55-1d2e3f4a5b6c",
                                    "email": "player@example.com",
                                },
                            }
                        ],
                        "total": 1,
                        "limit": 20,
                        "offset": 0,
                    },
                ),
                "empty": (
                    "Результатов пока нет",
                    {"items": [], "total": 0, "limit": 20, "offset": 0},
                ),
            },
        ),
        401: UNAUTHORIZED_BEARER,
    },
)
async def get_top_leaderboard(
    current_user: CurrentUser,
    game_name: Annotated[
        AllowedGames, Path(description="Идентификатор игры.", examples=["snake"])
    ],
    season_id: int = Query(..., description="ID сезона.", examples=[1]),
    seed: int = Query(..., description="Сид генерации уровня.", examples=[5]),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
    limit: int = Query(default=20, ge=1, le=100, description="Лимит выборки."),
    offset: int = Query(default=0, ge=0, description="Смещение выборки."),
):
    return await leaderboard_service.get_leaderboard(
        game_name, season_id, seed, limit, offset
    )
