from app.leaderboard.repositories import LeaderboardRepository


class LeaderboardService:
    def __init__(self, repository: LeaderboardRepository):
        self.repository = repository

    async def get_top_leaderboard(self, game_name: str, season_id: int, seed: int):
        return await self.repository.get_leaderbord_game_season(
            game_name, season_id, seed
        )
