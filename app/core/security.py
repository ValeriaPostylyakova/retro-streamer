import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret_key: str = Field(
        default="5582ac862f4296545e8b7638dda38ea1bd565a02285eae163230693cf1f7bf79"
    )
    jwt_issuer: str = Field(default="my-api")
    jwt_audience: str = Field(default="my-frontend")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 10
REFRESH_TOKEN_DAYS = 7

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


def create_access_token(
    user_id: UUID,
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "jti": str(uuid4()),
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[ALGORITHM],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={
            "require": [
                "sub",
                "iss",
                "aud",
                "iat",
                "exp",
                "jti",
                "type",
            ]
        },
    )

    if payload.get("type") != "access":
        raise InvalidTokenError("Wrong token type")

    return payload


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_DAYS * 24 * 60 * 60,
    )


def delete_refresh_token(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )
