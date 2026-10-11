from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.auth.models import User, UserSession
from app.auth.repositories import UserRepository
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.core.security import (
    REFRESH_TOKEN_DAYS,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def register_user(self, form_data: RegisterRequest):
        user = await self.repository.get_user_by_email(form_data.email)
        if user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )

        user = User(
            email=form_data.email,
            hashed_password=hash_password(form_data.password),
            role="default",
        )

        return await self.repository.create_user(user)

    async def authenticate_user(self, form_data: LoginRequest) -> TokenResponse:
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

        now = datetime.now(timezone.utc)
        refresh_token = create_refresh_token()

        user_session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=now + timedelta(days=REFRESH_TOKEN_DAYS),
        )

        await self.repository.create_user_session(user_session)

        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def rotate_refresh_token(self, refresh_token: str) -> TokenResponse:
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

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
