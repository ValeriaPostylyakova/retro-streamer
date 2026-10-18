from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Проверяет живое ли соединение перед отправкой запроса
)


sync_session_maker = sessionmaker(
    bind=sync_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


async def get_db():
    from app.auth.models import (
        User,  # noqa: F401
        UserSession,  # noqa: F401
    )
    from app.game_renders.models import GameRender  # noqa: F401
    from app.leaderboard.models import Leaderboard  # noqa: F401

    async with async_session_maker() as session:
        yield session
