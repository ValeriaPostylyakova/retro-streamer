from app.leaderboard.repositories import LeaderboardRepository
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
