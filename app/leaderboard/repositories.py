from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
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

        rn_column = (
            func.row_number()
            .over(
                partition_by=Leaderboard.user_id,
                order_by=[
                    Leaderboard.score.desc(),
                    Leaderboard.steps_count.asc(),
                    Leaderboard.created_at.desc(),
                ],
            )
            .label("rn")
        )

        best_records_subquery = (
            select(Leaderboard.id.label("leaderboard_id"), rn_column)
            .where(*where_clauses)
            .subquery()
        )

        stmt = (
            select(Leaderboard)
            .options(joinedload(Leaderboard.user))
            .join(
                best_records_subquery,
                Leaderboard.id == best_records_subquery.c.leaderboard_id,
            )
            .where(best_records_subquery.c.rn == 1)
            .order_by(
                Leaderboard.score.desc(),
                Leaderboard.steps_count.asc(),
                Leaderboard.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        records = result.scalars().unique().all()

        count_stmt = select(func.count(func.distinct(Leaderboard.user_id))).where(
            *where_clauses
        )
        total = await self.session.scalar(count_stmt) or 0

        return records, total

    async def save_leaderboard_record(
        self, user_id: UUID, render_id: UUID, score: int, game_name: str, seed: int
    ) -> None:

        stmt = insert(Leaderboard).values(
            user_id=user_id,
            render_id=render_id,
            score=score,
            game_name=game_name,
            season_id=settings.CURRENT_SEASON_ID,
            seed=seed,
        )

        safe_stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "render_id"])

        await self.session.execute(safe_stmt)
        await self.session.commit()

    async def get_unique_leaderboard(
        self, user_id: UUID, render_id: UUID
    ) -> Leaderboard | None:

        stmt = select(Leaderboard).where(
            Leaderboard.user_id == user_id,
            Leaderboard.render_id == render_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
