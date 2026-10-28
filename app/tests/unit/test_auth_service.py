from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.auth.models import User, UserSession
from app.auth.schemas import LoginRequest, RegisterRequest
from app.core.config import settings
from app.core.exceptions import ApplicationError


@pytest.mark.asyncio
async def test_register_user_success(auth_service, auth_repository, monkeypatch):
    user_id = uuid4()

    def create_user_side_effect(user: User) -> User:
        user.id = user_id
        return user

    auth_repository.create_user.side_effect = create_user_side_effect
    monkeypatch.setattr(
        "app.auth.services.hash_password", lambda password: "hashed:" + password
    )
    monkeypatch.setattr("app.auth.services.create_refresh_token", lambda: "refresh-123")
    monkeypatch.setattr(
        "app.auth.services.hash_refresh_token", lambda token: "hash:" + token
    )
    monkeypatch.setattr(
        "app.auth.services.create_access_token", lambda uid: "access:" + str(uid)
    )

    form = RegisterRequest(
        email="new-player@example.com",
        password="super-secret",
        confirm_password="super-secret",
    )

    created, access_token, refresh_token = await auth_service.register_user(form)

    assert created.id == user_id
    assert created.email == "new-player@example.com"
    assert created.hashed_password == "hashed:super-secret"
    assert access_token == f"access:{user_id}"
    assert refresh_token == "refresh-123"
    auth_repository.get_user_by_email.assert_awaited_once_with("new-player@example.com")
    auth_repository.create_user.assert_awaited_once()
    auth_repository.create_user_session.assert_awaited_once()
    session = auth_repository.create_user_session.await_args.args[0]
    assert isinstance(session, UserSession)
    assert session.user_id == user_id
    assert session.refresh_token_hash == "hash:refresh-123"
    assert session.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_conflict(
    auth_service, auth_repository, user
):
    auth_repository.get_user_by_email.return_value = user
    form = RegisterRequest(
        email=user.email,
        password="super-secret",
        confirm_password="super-secret",
    )

    with pytest.raises(ApplicationError) as exc_info:
        await auth_service.register_user(form)

    assert exc_info.value.status_code == 409
    auth_repository.create_user.assert_not_awaited()
    auth_repository.create_user_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_user_success(
    auth_service, auth_repository, user, monkeypatch
):
    auth_repository.get_user_by_email.return_value = user
    monkeypatch.setattr(
        "app.auth.services.verify_password",
        lambda password, hashed: (
            password == "super-secret" and hashed == user.hashed_password
        ),
    )
    monkeypatch.setattr("app.auth.services.create_refresh_token", lambda: "refresh-456")
    monkeypatch.setattr(
        "app.auth.services.hash_refresh_token", lambda token: "hash:" + token
    )
    monkeypatch.setattr(
        "app.auth.services.create_access_token", lambda uid: "access:" + str(uid)
    )

    result_user, access_token, refresh_token = await auth_service.authenticate_user(
        LoginRequest(email=user.email, password="super-secret")
    )

    assert result_user is user
    assert access_token == f"access:{user.id}"
    assert refresh_token == "refresh-456"
    auth_repository.create_user_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_authenticate_user_unknown_email_rejected(auth_service, auth_repository):
    auth_repository.get_user_by_email.return_value = None

    with pytest.raises(ApplicationError) as exc_info:
        await auth_service.authenticate_user(
            LoginRequest(email="missing@example.com", password="super-secret")
        )

    assert exc_info.value.status_code == 401
    auth_repository.create_user_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password_rejected(
    auth_service, auth_repository, user, monkeypatch
):
    auth_repository.get_user_by_email.return_value = user
    monkeypatch.setattr(
        "app.auth.services.verify_password", lambda password, hashed: False
    )

    with pytest.raises(ApplicationError) as exc_info:
        await auth_service.authenticate_user(
            LoginRequest(email=user.email, password="wrong-password")
        )

    assert exc_info.value.status_code == 401
    auth_repository.create_user_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_inactive_user_cannot_authenticate(
    auth_service, auth_repository, user, monkeypatch
):
    user.is_active = False
    auth_repository.get_user_by_email.return_value = user
    monkeypatch.setattr(
        "app.auth.services.verify_password", lambda password, hashed: True
    )

    with pytest.raises(ApplicationError) as exc_info:
        await auth_service.authenticate_user(
            LoginRequest(email=user.email, password="super-secret")
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Пользователь заблокирован"
    auth_repository.create_user_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_rotate_refresh_token_success_uses_configured_lifetime(
    auth_service, auth_repository, monkeypatch
):
    user_id = uuid4()
    auth_repository.rotate_refresh_token.return_value = user_id
    monkeypatch.setattr("app.auth.services.create_refresh_token", lambda: "new-refresh")
    monkeypatch.setattr(
        "app.auth.services.hash_refresh_token", lambda token: "hash:" + token
    )
    monkeypatch.setattr(
        "app.auth.services.create_access_token", lambda uid: "access:" + str(uid)
    )

    access_token, refresh_token = await auth_service.rotate_refresh_token("old-refresh")

    assert access_token == f"access:{user_id}"
    assert refresh_token == "new-refresh"
    kwargs = auth_repository.rotate_refresh_token.await_args.kwargs
    assert kwargs["old_token_hash"] == "hash:old-refresh"
    assert kwargs["new_token_hash"] == "hash:new-refresh"
    assert kwargs["expires_at"] > kwargs["now"]
    assert kwargs["expires_at"] - kwargs["now"] == timedelta(
        days=settings.REFRESH_TOKEN_DAYS
    )


@pytest.mark.asyncio
async def test_rotate_refresh_token_invalid_token_rejected(
    auth_service, auth_repository, monkeypatch
):
    auth_repository.rotate_refresh_token.return_value = None
    monkeypatch.setattr("app.auth.services.create_refresh_token", lambda: "new-refresh")
    monkeypatch.setattr(
        "app.auth.services.hash_refresh_token", lambda token: "hash:" + token
    )

    with pytest.raises(ApplicationError) as exc_info:
        await auth_service.rotate_refresh_token("invalid-refresh")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_hashed_refresh_token(
    auth_service, auth_repository, monkeypatch
):
    monkeypatch.setattr(
        "app.auth.services.hash_refresh_token", lambda token: "hash:" + token
    )

    await auth_service.logout("refresh-to-revoke")

    auth_repository.revoke_refresh_token.assert_awaited_once_with(
        refresh_token_hash="hash:refresh-to-revoke"
    )
