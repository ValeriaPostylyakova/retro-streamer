from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.users.dependencies import CurrentUser, get_users_service
from app.users.schemas import Token, UserResponse
from app.users.services import UserService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends(get_users_service),
):
    return await user_service.authenticate_user(form_data)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: CurrentUser):
    return current_user
