from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserCreate(BaseModel):
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


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class TokenData(BaseModel):
    email: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
