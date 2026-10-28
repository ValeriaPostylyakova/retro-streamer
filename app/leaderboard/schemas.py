from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class UserNestedSchema(BaseResponse):
    id: UUID
    email: str


class LeaderboardResponse(BaseResponse):
    id: int
    game_name: str
    score: int
    steps_count: int
    created_at: datetime

    user: UserNestedSchema


class LeaderboardCreateDTO(BaseModel):
    user_id: UUID
    game_name: str
    score: int = Field(ge=0, le=2048)
    steps_count: int
    render_id: UUID
    seed: int
