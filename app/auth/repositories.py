from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user: User) -> User:
        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user_session(self, user_session: UserSession) -> UserSession:
        self.session.add(user_session)

        await self.session.commit()
        await self.session.refresh(user_session)
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

            result = await self.session.execute(stmt)
            user_id = result.scalar_one_or_none()

            if user_id is None:
                await self.session.rollback()
                return None

            await self.session.commit()
            return user_id

        except Exception:
            await self.session.rollback()
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
                    UserSession.expires_at > datetime.now(UTC),
                )
                .values(
                    revoked_at=datetime.now(UTC),
                )
                .returning(UserSession.id)
            )

            result = await self.session.execute(stmt)
            session_id = result.scalar_one_or_none()

            if session_id is None:
                await self.session.rollback()
                return False

            await self.session.commit()
            return True

        except Exception:
            await self.session.rollback()
            raise
