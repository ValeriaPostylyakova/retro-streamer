from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.base_seeder import BaseSeeder


class LeaderboardSeeder(BaseSeeder):
    async def seed(self, session: AsyncSession) -> None:
        # result = await session.execute(select(GameRender))
        # renders = result.scalars().all()

        # if not renders:
        #     print(" No game renders found. Skipping leaderboard seed.")
        #     return

        # for render in renders:
        #     for _ in range(random.randint(1, 2)):
        #         leaderboard_entry = Leaderboard(
        #             user_id=render.user_id,
        #             game_name=render.game_name,
        #             score=random.randint(500, 100000),
        #             render_id=render.id,
        #         )
        #         session.add(leaderboard_entry)

        # print("-> Leaderboard seeded successfully.")
        pass
