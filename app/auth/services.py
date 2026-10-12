from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.auth.models import User, UserSession
from app.auth.repositories import AuthRepository
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
)
from app.core.security import (
    REFRESH_TOKEN_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class AuthService:
    def __init__(self, auth_repository: AuthRepository):
        self.repository = auth_repository

    async def _generate_tokens_and_session(self, user_id: UUID) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        refresh_token = create_refresh_token()

        user_session = UserSession(
            user_id=user_id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=now + timedelta(days=REFRESH_TOKEN_DAYS),
        )
        await self.repository.create_user_session(user_session)

        access_token = create_access_token(user_id)
        return access_token, refresh_token

    async def register_user(self, form_data: RegisterRequest) -> tuple[User, str, str]:
        user = await self.repository.get_user_by_email(form_data.email)
        if user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )

        new_user = User(
            email=form_data.email,
            hashed_password=hash_password(form_data.password),
            role="default",
        )

        created_user = await self.repository.create_user(new_user)

        access_token, refresh_token = await self._generate_tokens_and_session(
            created_user.id
        )
        return created_user, access_token, refresh_token

    async def authenticate_user(self, form_data: LoginRequest) -> tuple[User, str, str]:
        user = await self.repository.get_user_by_email(form_data.email)
        if user is None or not verify_password(
            form_data.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь заблокирован",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token, refresh_token = await self._generate_tokens_and_session(user.id)
        return user, access_token, refresh_token

    async def rotate_refresh_token(self, refresh_token: str) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=REFRESH_TOKEN_DAYS)

        new_refresh_token = create_refresh_token()

        user_id = await self.repository.rotate_refresh_token(
            old_token_hash=hash_refresh_token(refresh_token),
            new_token_hash=hash_refresh_token(new_refresh_token),
            now=now,
            expires_at=expires_at,
        )

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(user_id)

        return access_token, new_refresh_token

    async def logout(self, refresh_token: str) -> None:
        await self.repository.revoke_refresh_token(
            refresh_token_hash=hash_refresh_token(refresh_token),
        )

    async def get_user_with_game_renders(self, user_id: UUID):
        return await self.repository.get_user_with_game_renders(user_id)
