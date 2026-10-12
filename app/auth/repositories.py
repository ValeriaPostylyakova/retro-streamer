from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User, UserSession


class AuthRepository:
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
        try:
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
            user_id = result.scalar_one_or_none()

            if user_id is None:
                await self.db.rollback()
                return None

            await self.db.commit()
            return user_id

        except Exception:
            await self.db.rollback()
            raise

    async def revoke_refresh_token(
        self,
        refresh_token_hash: str,
    ) -> bool:
        try:
            stmt = (
                update(UserSession)
                .where(
                    UserSession.refresh_token_hash == refresh_token_hash,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
                .values(
                    revoked_at=datetime.now(timezone.utc),
                )
                .returning(UserSession.id)
            )

            result = await self.db.execute(stmt)
            session_id = result.scalar_one_or_none()

            if session_id is None:
                await self.db.rollback()
                return False

            await self.db.commit()
            return True

        except Exception:
            await self.db.rollback()
            raise

    async def get_user_with_game_renders(self, user_id: UUID):
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.game_renders))
        )
        user_result = await self.db.execute(stmt)
        return user_result.scalar_one_or_none()
