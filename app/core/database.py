from contextlib import contextmanager

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


async def get_async_session():
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_session():
    session = sync_session_maker()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
