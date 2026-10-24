from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_renders.models import GameRender


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
