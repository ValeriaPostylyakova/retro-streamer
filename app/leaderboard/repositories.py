from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.game_renders.models import GameRender
from app.leaderboard.models import Leaderboard


class LeaderboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_leaderbord_game_season(
        self, game_name: str, season_id: int, seed: int
    ) -> Sequence[Leaderboard]:
        stmt = (
            select(Leaderboard)
            .join(Leaderboard.render)
            .options(joinedload(Leaderboard.user), joinedload(Leaderboard.render))
            .where(
                Leaderboard.game_name == game_name,
                GameRender.seed == seed,
                GameRender.season_id == season_id,
            )
            .order_by(Leaderboard.scope.desc(), Leaderboard.created_at.desc())
        )

        result = await self.session.execute(stmt)

        leaderboard_records = result.scalars().unique().all()
        return leaderboard_records
