from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.base import BaseResponse


class RegisterRequest(BaseModel):
    email: EmailStr = Field(
        ...,
    )
    password: str = Field(min_length=8, max_length=50)
    confirm_password: str = Field(min_length=8, max_length=50)

    @model_validator(mode="after")
    def validate_password(self):
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        return self


class UserResponse(BaseResponse):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None
