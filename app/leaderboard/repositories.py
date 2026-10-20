from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.game_renders.models import GameRender
from app.leaderboard.models import Leaderboard


class LeaderboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_game_season_records(
        self, game_name: str, season_id: int, seed: int, limit: int, offset: int
    ) -> tuple[Sequence[Leaderboard], int]:

        where_clauses = [
            Leaderboard.game_name == game_name,
            GameRender.seed == seed,
            GameRender.season_id == season_id,
        ]

        stmt = (
            select(Leaderboard)
            .join(Leaderboard.render)
            .options(joinedload(Leaderboard.user), joinedload(Leaderboard.render))
            .where(*where_clauses)
            .order_by(Leaderboard.score.desc(), Leaderboard.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        records = result.scalars().unique().all()

        count_stmt = (
            select(func.count(Leaderboard.id))
            .join(Leaderboard.render)
            .where(*where_clauses)
        )
        total = await self.session.scalar(count_stmt) or 0

        return records, total

    async def save_leaderboard_record(
        self, user_id: UUID, render_id: UUID, score: int, game_name: str
    ) -> None:

        stmt = insert(Leaderboard).values(
            user_id=user_id, render_id=render_id, score=score, game_name=game_name
        )

        safe_stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "render_id"])

        await self.session.execute(safe_stmt)
        await self.session.commit()
