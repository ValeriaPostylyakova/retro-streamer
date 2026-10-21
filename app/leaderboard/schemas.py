from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class UserNestedSchema(BaseResponse):
    id: UUID
    email: str


class GameRenderNestedSchema(BaseResponse):
    id: UUID
    s3_key: str


class LeaderboardResponse(BaseResponse):
    id: int
    game_name: str
    score: int
    created_at: datetime

    user: UserNestedSchema
    render: GameRenderNestedSchema


class LeaderboardCreateDTO(BaseModel):
    user_id: UUID
    game_name: str
    score: int = Field(ge=0, le=100)
    render_id: UUID
    seed: int
