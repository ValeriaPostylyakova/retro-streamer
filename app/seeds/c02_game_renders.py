import random

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.game_renders.models import GameRender
from app.seeds.base_seeder import BaseSeeder
from app.users.models import User

fake = Faker()

RETRO_GAMES = ["Super Mario Bros", "Sonic the Hedgehog", "Pac-Man", "Doom", "Tetris"]


class GameRenderSeeder(BaseSeeder):
    async def seed(self, session: AsyncSession) -> None:
        result = await session.execute(select(User.id))
        user_ids = result.scalars().all()

        if not user_ids:
            print(" No users found. Skipping game renders seed.")
            return

        for _ in range(25):
            game_name = random.choice(RETRO_GAMES)
            user_id = random.choice(user_ids)

            render = GameRender(
                user_id=user_id,
                game_name=game_name,
                commands_hash=fake.md5(raw_output=False),
                s3_key=f"renders/{user_id}/{game_name.lower().replace(' ', '_')}_{fake.uuid4()}.mp4",
            )
            session.add(render)

        print("-> Game renders seeded successfully.")
