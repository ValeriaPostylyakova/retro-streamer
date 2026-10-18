from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class GameRenderRequest(BaseModel):
    commands: list[str] = Field(
        ...,
        max_length=50,
        min_length=2,
        examples=[
            "up",
            "down",
            "left",
            "right",
        ],
    )
    seed: int = 42


class GameRules(BaseModel):
    field_size: int
    max_commands: int
    opposite_directions: dict[str, str]


class GameInitialState(BaseModel):
    snake_body: list[list[int]]
    current_direction: str
    food_position: list[int]


class GameInfoResponse(BaseModel):
    seed: int
    rules: GameRules
    initial_state: GameInitialState


class GameRenderList(BaseModel):
    commands_hash: str
    s3_key: str


class RenderStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"


class GameRenderResponse(BaseModel):
    status: RenderStatus
    cached: bool
    task_id: str | None = None
    download_url: str | None = None


class TaskStatusResponse(BaseResponse):
    task_id: str
    status: str
    progress: int
    result_data: Any | None = None
