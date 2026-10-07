import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Импортируем настройки и метадату из вашего FastAPI-приложения
from app.core.config import settings
from app.core.database import Base

# Это объект конфигурации Alembic, который предоставляет
# доступ к значениям внутри файла alembic.ini.
config = context.config

# Динамически подставляем URL базы данных из вашего файла настроек (settings)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Настройка логирования на основе файла конфигурации
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Передаем метадату моделей, чтобы работал автогенератор миграций (--autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме.

    Этот режим выполняется без создания полноценного движка подключения,
    например, для генерации SQL-скриптов в файл.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Вспомогательный синхронный контекст для выполнения миграций."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Создание асинхронного движка и выполнение миграций в online-режиме."""
    section = config.get_section(config.config_ini_section, {})

    # Жестко гарантируем, что URL берется напрямую из settings вашего FastAPI приложения,
    # даже если в alembic.ini прописано что-то другое
    section["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Так как alembic внутри синхронный, запускаем его через run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (с подключением к базе данных)."""

    # Безопасный перехват и использование Event Loop, чтобы избежать конфликтов в Docker
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если цикл событий уже запущен
        loop.create_task(run_async_migrations())
    else:
        # Стандартный запуск чистого цикла для контейнера миграций
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
