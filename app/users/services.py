from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token, verify_password
from app.users.repositories import UserRepository
from app.users.schemas import Token, UserCreate


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> Token:
        user = await self.repository.get_user_by_email(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(user.id)

        return Token(access_token=access_token, token_type="bearer")

    async def register_user(self, user_data: UserCreate):
        existing_user = await self.repository.get_user_by_email(user_data.email)

        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")
