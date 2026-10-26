from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_sync_session
from app.game_renders.models import GameRender
from app.leaderboard.models import Leaderboard


class GameRenderRepository:
    def __init__(self, session: AsyncSession):
        self.db_session = session

    async def get_render_by_commands_hash(
        self, commands_hash: str
    ) -> GameRender | None:
        stmt = select(GameRender).where(GameRender.commands_hash == commands_hash)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def get_render_by_id(self, render_id: UUID) -> GameRender | None:
        stmt = select(GameRender).where(GameRender.id == render_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def save_game_results_to_sync_db(
        user_id: UUID,
        game_name: str,
        seed: int,
        score: int,
        steps_count: int,
        hash_key: str,
        object_name: str,
    ) -> UUID:
        with get_sync_session() as session:
            new_render = GameRender(
                game_name=game_name,
                seed=seed,
                score=score,
                steps_count=steps_count,
                season_id=settings.CURRENT_SEASON_ID,
                commands_hash=hash_key,
                s3_key=object_name,
            )
            session.add(new_render)
            session.flush()

            stmt = (
                insert(Leaderboard)
                .values(
                    user_id=user_id,
                    game_name=game_name,
                    score=score,
                    steps_count=steps_count,
                    render_id=new_render.id,
                    season_id=settings.CURRENT_SEASON_ID,
                    seed=seed,
                )
                .on_conflict_do_nothing(index_elements=["user_id", "render_id"])
            )

            session.execute(stmt)
            session.commit()
            return new_render.id
