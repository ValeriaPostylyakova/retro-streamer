from fastapi import APIRouter, Cookie, Depends, Response, status

from app.auth.dependencies import CurrentUser, get_auth_service
from app.auth.schemas import (
    BaseUser,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserDetailResponse,
    UserResponse,
)
from app.auth.services import AuthService
from app.core.security import delete_refresh_token, set_refresh_cookie

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
async def register(
    response: Response,
    form_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    created_user, access_token, refresh_token = await auth_service.register_user(
        form_data
    )

    set_refresh_cookie(response, refresh_token)

    return UserResponse(
        tokens=TokenResponse(
            access_token=access_token,
            token_type="bearer",
        ),
        user=BaseUser(
            id=created_user.id, email=created_user.email, role=created_user.role
        ),
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Вход в систему",
)
async def login_for_access_token(
    response: Response,
    form_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    user, access_token, refresh_token = await auth_service.authenticate_user(form_data)

    set_refresh_cookie(response, refresh_token)

    return UserResponse(
        tokens=TokenResponse(
            access_token=access_token,
            token_type="bearer",
        ),
        user=BaseUser(id=user.id, email=user.email, role=user.role),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление refresh токена",
)
async def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service),
):
    if refresh_token:
        access_token, new_refresh_token = await auth_service.rotate_refresh_token(
            refresh_token
        )

        set_refresh_cookie(response, new_refresh_token)
        return TokenResponse(access_token=access_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
)
async def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:

    if refresh_token:
        await auth_service.logout(refresh_token)

    delete_refresh_token(response)


@router.get(
    "/me",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение информации о пользователе",
)
async def read_users_me(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_user_with_game_renders(current_user.id)
