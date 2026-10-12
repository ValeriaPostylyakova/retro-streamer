from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    from app.auth.models import (
        User,  # noqa: F401
        UserSession,  # noqa: F401
    )
    from app.game_renders.models import GameRender  # noqa: F401
    from app.leaderboard.models import Leaderboard  # noqa: F401

    async with async_session_maker() as session:
        yield session
