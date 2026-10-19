from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseResponse


class UserNestedSchema(BaseResponse):
    id: UUID
    email: str
    role: str
    is_active: bool


class GameRenderNestedSchema(BaseResponse):
    id: UUID
    seed: int
    season_id: int
    game_name: str
    s3_key: str


class LeaderboardResponse(BaseResponse):
    id: int
    game_name: str
    scope: int
    created_at: datetime

    user: UserNestedSchema
    render: GameRenderNestedSchema
