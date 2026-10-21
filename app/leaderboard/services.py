from uuid import UUID

from app.leaderboard.models import Leaderboard
from app.leaderboard.repositories import LeaderboardRepository
from app.leaderboard.schemas import LeaderboardCreateDTO
from app.schemas.common import LimitOffsetResponse


class LeaderboardService:
    def __init__(self, repository: LeaderboardRepository):
        self.repository = repository

    async def get_leaderboard(
        self, game_name: str, season_id: int, seed: int, limit: int, offset: int
    ):

        records, total = await self.repository.get_game_season_records(
            game_name=game_name,
            season_id=season_id,
            seed=seed,
            limit=limit,
            offset=offset,
        )

        return LimitOffsetResponse(
            items=list(records), total=total, limit=limit, offset=offset
        )

    async def save_leaderboard_record(self, dto: LeaderboardCreateDTO):
        await self.repository.save_leaderboard_record(
            user_id=dto.user_id,
            render_id=dto.render_id,
            score=dto.score,
            game_name=dto.game_name,
            seed=dto.seed,
        )

    async def get_user_render_leaderboard(
        self, user_id: UUID, render_id: UUID
    ) -> Leaderboard | None:
        return await self.repository.get_unique_leaderboard(user_id, render_id)
