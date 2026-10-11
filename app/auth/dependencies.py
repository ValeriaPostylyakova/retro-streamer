from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.repositories import UserRepository
from app.auth.services import UserService
from app.core.database import get_db
from app.core.security import (
    decode_access_token,
    oauth2_scheme,
    unauthorized,
)


async def get_users_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_users_service(
    repository: UserRepository = Depends(get_users_repository),
) -> UserService:
    return UserService(repository)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    users_repo: Annotated[UserRepository, Depends(get_users_repository)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
    except (InvalidTokenError, KeyError, TypeError):
        raise unauthorized()

    user = await users_repo.get_user_by_id(user_id)

    if user is None or user.is_active is False:
        raise unauthorized()

    return user


if TYPE_CHECKING:
    from app.auth.models import User

CurrentUser = Annotated[
    "User",
    Depends(get_current_user),
]
