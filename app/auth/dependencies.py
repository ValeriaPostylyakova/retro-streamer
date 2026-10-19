from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.repositories import AuthRepository
from app.auth.services import AuthService
from app.core.database import get_async_session
from app.core.security import (
    decode_access_token,
    oauth2_scheme,
    unauthorized,
)


async def get_auth_repository(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> AuthRepository:
    return AuthRepository(db)


def get_auth_service(
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(repository)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_repo: Annotated[AuthRepository, Depends(get_auth_repository)],
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
    except (InvalidTokenError, KeyError, TypeError):
        raise unauthorized()

    user = await auth_repo.get_user_by_id(user_id)

    if user is None or user.is_active is False:
        raise unauthorized()

    return user


if TYPE_CHECKING:
    from app.auth.models import User

CurrentUser = Annotated[
    "User",
    Depends(get_current_user),
]
