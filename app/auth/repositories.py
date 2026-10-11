from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserSession


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: User) -> User:
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_user_session(self, user_session: UserSession) -> UserSession:
        self.db.add(user_session)

        await self.db.commit()
        await self.db.refresh(user_session)
        return user_session

    async def rotate_refresh_token(
        self,
        old_token_hash: str,
        new_token_hash: str,
        now: datetime,
        expires_at: datetime,
    ) -> UUID | None:
        stmt = (
            update(UserSession)
            .where(
                UserSession.refresh_token_hash == old_token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .values(
                refresh_token_hash=new_token_hash,
                expires_at=expires_at,
            )
            .returning(UserSession.user_id)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
