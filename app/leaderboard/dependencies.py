from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.leaderboard.repositories import LeaderboardRepository
from app.leaderboard.services import LeaderboardService


def get_leaderboard_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    return LeaderboardRepository(session)


def get_leaderboard_service(
    repository: LeaderboardRepository = Depends(get_leaderboard_repository),
):
    return LeaderboardService(repository)
