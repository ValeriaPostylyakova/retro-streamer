from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class BaseSeeder(ABC):
    @abstractmethod
    async def seed(self, session: AsyncSession) -> None:
        pass
