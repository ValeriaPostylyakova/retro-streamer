from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.openapi_docs import (
    DELETE_REFRESH_COOKIE_HEADER,
    EXAMPLE_ACCESS_TOKEN,
    EXAMPLE_USER_RESPONSE,
    SET_REFRESH_COOKIE_HEADER,
    WWW_AUTHENTICATE_HEADER,
    detail_error,
    ok_examples,
)
from app.auth.dependencies import get_auth_service
from app.auth.schemas import (
    BaseUser,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.services import AuthService
from app.core.exceptions import ApplicationError
from app.core.security import delete_refresh_token, set_refresh_cookie

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description=(
        "Создаёт учётную запись и автоматически выполняет вход.\n\n"
        "Access-токен возвращается в теле ответа, refresh-токен — в HttpOnly-cookie `refresh_token`."
    ),
    responses={
        201: ok_examples(
            "Пользователь создан.",
            {"created": ("Успешная регистрация", EXAMPLE_USER_RESPONSE)},
            headers=SET_REFRESH_COOKIE_HEADER,
        ),
        409: detail_error(
            "Пользователь с таким email уже существует.",
            {
                "email_exists": (
                    "Email уже занят",
                    "Пользователь с таким email уже существует",
                )
            },
            headers=WWW_AUTHENTICATE_HEADER,
        ),
    },
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
        access_token=access_token,
        token_type="bearer",
        user=BaseUser(
            id=created_user.id, email=created_user.email, role=created_user.role
        ),
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Вход по email и паролю",
    description=(
        "Аутентифицирует пользователя и создаёт новую сессию.\n\n"
        "Ответ унифицирован: по сообщению об ошибке нельзя определить существование email в системе."
    ),
    responses={
        200: ok_examples(
            "Вход выполнен успешно.",
            {"ok": ("Успешный вход", EXAMPLE_USER_RESPONSE)},
            headers=SET_REFRESH_COOKIE_HEADER,
        ),
        401: detail_error(
            "Неверные учётные данные или пользователь заблокирован.",
            {
                "bad_credentials": (
                    "Неверный email или пароль",
                    "Неверный email или пароль",
                ),
                "user_blocked": (
                    "Пользователь заблокирован",
                    "Пользователь заблокирован",
                ),
            },
            headers=WWW_AUTHENTICATE_HEADER,
        ),
    },
)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    user, access_token, refresh_token = await auth_service.authenticate_user(form_data)
    set_refresh_cookie(response, refresh_token)
    return UserResponse(
        access_token=access_token,
        token_type="bearer",
        user=BaseUser(id=user.id, email=user.email, role=user.role),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление пары токенов",
    description=(
        "Выдаёт новый access-токен и ротирует refresh-токен текущей сессии.\n\n"
        "Токен извлекается автоматически из cookie `refresh_token`."
    ),
    responses={
        200: ok_examples(
            "Токены обновлены.",
            {
                "ok": (
                    "Новый access-токен",
                    {"access_token": EXAMPLE_ACCESS_TOKEN, "token_type": "bearer"},
                )
            },
            headers=SET_REFRESH_COOKIE_HEADER,
        ),
        401: detail_error(
            "Refresh-токен отсутствует или недействителен.",
            {
                "no_cookie": ("Cookie не передана", "Refresh token отсутствует"),
                "invalid_token": ("Токен недействителен", "Неверный refresh token"),
            },
        ),
    },
)
async def refresh_token(
    response: Response,
    refresh_token: str = Cookie(
        None, description="Текущий refresh-токен (cookie `refresh_token`)."
    ),
    auth_service: AuthService = Depends(get_auth_service),
):
    if not refresh_token:
        raise ApplicationError(detail="Refresh token отсутствует", status_code=401)
    access_token, new_refresh_token = await auth_service.rotate_refresh_token(
        refresh_token
    )
    set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=access_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы",
    description="Завершает текущую сессию (отзывает refresh-токен) и удаляет авторизационную cookie.",
    responses={
        204: {
            "description": "Сессия завершена, cookie удалена. Операция идемпотентна.",
            "headers": DELETE_REFRESH_COOKIE_HEADER,
        },
    },
)
async def logout(
    response: Response,
    refresh_token: str = Cookie(None, description="Refresh-токен текущей сессии."),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    if refresh_token:
        await auth_service.logout(refresh_token)
    delete_refresh_token(response)
