import pytest

from app.core.config import settings
from app.core.exceptions import ApplicationError

AUTH_PREFIX = "/api/v1/auth"


@pytest.mark.asyncio
async def test_register_returns_user_and_access_token(client, auth_service, user):
    auth_service.register_user.return_value = (user, "access-token", "refresh-token")

    response = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": user.email,
            "password": "strong-password",
            "confirm_password": "strong-password",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["id"] == str(user.id)
    assert body["user"]["email"] == user.email
    assert body["tokens"]["access_token"] == "access-token"
    assert body["tokens"]["token_type"] == "bearer"
    auth_service.register_user.assert_awaited_once()

    cookie = response.headers["set-cookie"].lower()
    assert "refresh_token=refresh-token" in cookie
    assert "httponly" in cookie
    assert f"max-age={settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60}" in cookie


@pytest.mark.asyncio
async def test_register_rejects_mismatched_passwords(client, auth_service):
    response = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": "player@example.com",
            "password": "strong-password",
            "confirm_password": "different-password",
        },
    )

    assert response.status_code == 422
    auth_service.register_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_maps_duplicate_email_to_conflict(client, auth_service):
    auth_service.register_user.side_effect = ApplicationError(
        "Пользователь с таким email уже существует",
        status_code=409,
    )

    response = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": "player@example.com",
            "password": "strong-password",
            "confirm_password": "strong-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Пользователь с таким email уже существует"


@pytest.mark.asyncio
async def test_login_returns_tokens_and_sets_refresh_cookie(client, auth_service, user):
    auth_service.authenticate_user.return_value = (
        user,
        "access-token",
        "refresh-token",
    )

    response = await client.post(
        f"{AUTH_PREFIX}/login",
        data={"username": user.email, "password": "strong-password"},
    )

    assert response.status_code == 200
    assert response.json()["tokens"]["access_token"] == "access-token"
    assert response.json()["user"]["email"] == user.email
    assert "refresh_token=refresh-token" in response.headers["set-cookie"]
    auth_service.authenticate_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(client, auth_service):
    auth_service.authenticate_user.side_effect = ApplicationError(
        "Неверный email или пароль",
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )

    response = await client.post(
        f"{AUTH_PREFIX}/login",
        data={"username": "player@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_refresh_rotates_cookie_and_returns_access_token(client, auth_service):
    auth_service.rotate_refresh_token.return_value = (
        "new-access-token",
        "new-refresh-token",
    )

    response = await client.post(
        f"{AUTH_PREFIX}/refresh",
        cookies={"refresh_token": "old-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "token_type": "bearer",
    }
    assert "refresh_token=new-refresh-token" in response.headers["set-cookie"]
    auth_service.rotate_refresh_token.assert_awaited_once_with("old-refresh-token")


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_token(client, auth_service):
    auth_service.rotate_refresh_token.side_effect = ApplicationError(
        "Неверный refresh token",
        status_code=401,
    )

    response = await client.post(
        f"{AUTH_PREFIX}/refresh",
        cookies={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный refresh token"


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(client, auth_service):
    response = await client.post(f"{AUTH_PREFIX}/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token отсутствует"
    auth_service.rotate_refresh_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_revokes_cookie_token_and_returns_no_content(client, auth_service):
    response = await client.post(
        f"{AUTH_PREFIX}/logout",
        cookies={"refresh_token": "refresh-token"},
    )

    assert response.status_code == 204
    auth_service.logout.assert_awaited_once_with("refresh-token")
    assert "refresh_token=" in response.headers["set-cookie"]


@pytest.mark.asyncio
async def test_logout_without_cookie_is_idempotent(client, auth_service):
    response = await client.post(f"{AUTH_PREFIX}/logout")

    assert response.status_code == 204
    auth_service.logout.assert_not_awaited()
