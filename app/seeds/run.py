import asyncio
import sys
import traceback

from sqlalchemy import delete

from app.auth.models import User
from app.core.database import async_session_maker
from app.game_renders.models import GameRender
from app.leaderboard.models import Leaderboard
from app.seeds.c01_users import UserSeeder
from app.seeds.c02_game_renders import GameRenderSeeder
from app.seeds.c03_leaderboard import LeaderboardSeeder

SEEDERS = [
    UserSeeder(),
    GameRenderSeeder(),
    LeaderboardSeeder(),
]


async def clean_database(session) -> None:
    print(" Cleaning old test data...")

    await session.execute(delete(Leaderboard))
    await session.execute(delete(GameRender))
    await session.execute(delete(User))

    await session.flush()
    print(" Database clean!")


async def main():
    print(" Starting database seeding...")
    async with async_session_maker() as session:
        try:
            await clean_database(session)

            for seeder in SEEDERS:
                await seeder.seed(session)

            await session.commit()
            print(" All seeds completed successfully!")

        except Exception:
            await session.rollback()
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
