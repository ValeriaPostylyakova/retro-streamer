from fastapi import APIRouter, Depends, status

from app.auth.dependencies import CurrentUser, get_users_service
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.auth.services import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    form_data: RegisterRequest,
    user_service: UserService = Depends(get_users_service),
):
    return await user_service.register_user(form_data)


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: LoginRequest,
    user_service: UserService = Depends(get_users_service),
):
    return await user_service.authenticate_user(form_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    user_service: UserService = Depends(get_users_service),
):
    return await user_service.rotate_refresh_token(refresh_token)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user
