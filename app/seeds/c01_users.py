from argon2 import PasswordHasher
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.base_seeder import BaseSeeder
from app.users.models import User

fake = Faker(["ru_RU"])
ph = PasswordHasher()


class UserSeeder(BaseSeeder):
    async def seed(self, session: AsyncSession) -> None:
        common_password = ph.hash("user_password")

        for _ in range(10):
            profile = fake.simple_profile()
            user = User(
                email=profile["mail"],
                hashed_password=common_password,
                role="default",
            )
            session.add(user)

        print("-> Users seeded successfully.")
