from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.models import User
from app.auth.services import AuthService
from app.dependencies.rate_limiter import role_rate_limiter
from app.game_renders.dependencies import get_game_render_service
from app.main import app


@pytest.fixture
def user() -> User:
    """Универсальный пользователь для всех тестов (API и Unit)."""
    return User(
        id=uuid4(),
        email="player@example.com",
        hashed_password="test-password-hash",
        role="default",
        is_active=True,
    )


@pytest.fixture
def auth_repository() -> AsyncMock:
    repository = AsyncMock()
    repository.get_user_by_email.return_value = None
    repository.create_user_session.return_value = None
    repository.rotate_refresh_token.return_value = None
    repository.revoke_refresh_token.return_value = True
    return repository


@pytest.fixture
def auth_service(request, auth_repository: AsyncMock):
    """Возвращает реальный сервис для папки unit, и Мок для папки api."""
    if hasattr(request, "path") and "unit" in request.path.parts:
        return AuthService(auth_repository)
    return AsyncMock(spec=AuthService)


@pytest.fixture
def render_service() -> AsyncMock:
    """Глобальный мок сервиса рендеров для API тестов."""
    service = AsyncMock()
    service.process_game_render = AsyncMock()
    service.get_status_task = AsyncMock()
    service.download_file = AsyncMock()
    return service


@pytest_asyncio.fixture(loop_scope="function")
async def client(request, user):
    """Универсальный клиент FastAPI для API-тестов."""

    async def dummy_rate_limiter():
        return True

    previous_overrides = app.dependency_overrides.copy()

    try:
        app.dependency_overrides[role_rate_limiter] = dummy_rate_limiter
        app.dependency_overrides[get_current_user] = lambda: user

        if "auth_service" in request.fixturenames:
            auth_mock = request.getfixturevalue("auth_service")
            app.dependency_overrides[get_auth_service] = lambda: auth_mock

        if "render_service" in request.fixturenames:
            render_mock = request.getfixturevalue("render_service")
            app.dependency_overrides[get_game_render_service] = lambda: render_mock

        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
