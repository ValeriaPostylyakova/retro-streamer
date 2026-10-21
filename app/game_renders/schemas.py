from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class SnakeRenderRequest(BaseModel):
    commands: list[Literal["up", "down", "left", "right"]] = Field(
        ...,
        max_length=50,
        min_length=2,
        examples=[["up", "down", "left", "right"]],
    )
    seed: int = 5
    game_name: str = "snake"


class TetrisRenderRequest(BaseModel):
    commands: list[
        Literal[
            "left",
            "right",
            "rotate",
            "drop",
            "none",
        ]
    ] = Field(
        ...,
        max_length=80,
        min_length=2,
        examples=[
            "left",
            "right",
            "rotate",
            "drop",
            "none",
        ],
    )
    seed: int = 5
    game_name: str = "tetris"


class TetrisRules(BaseModel):
    field_size: tuple[int, int]
    max_commands: int = 80
    available_commands: list[str] = ["left", "right", "rotate", "drop", "none"]


class TetrisInitialState(BaseModel):
    board: list[list[int]]


class SnakeRules(BaseModel):
    field_size: int
    max_commands: int = 50
    opposite_directions: dict[str, str]
    available_commands: list[str] = ["up", "down", "left", "right"]


class SnakeInitialState(BaseModel):
    snake_body: list[list[int]]
    current_direction: str
    food_position: list[int]


class SnakeInfoResponse(BaseModel):
    seed: int
    rules: SnakeRules
    initial_state: SnakeInitialState


class TetrisInfoResponse(BaseModel):
    seed: int
    rules: TetrisRules
    initial_state: TetrisInitialState


class GameRenderList(BaseModel):
    commands_hash: str
    s3_key: str


class RenderStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"


class GameRenderResponse(BaseModel):
    status: RenderStatus
    task_id: str


class GameRenderResponseCache(BaseModel):
    status: str = RenderStatus.SUCCESS
    score: int
    render_id: UUID
    download_url: str

    expires_in: int = 300


class GameRenderResponseProcessing(BaseModel):
    status: str = RenderStatus.PENDING
    detail: str = "Обработка задачи с этими командами находится в процессе"


class GameRenderResultDTO(BaseModel):
    render_id: UUID
    score: int
    download_url: str


class TaskStatusResponse(BaseResponse):
    task_id: str
    status: str
    progress: int
    result: GameRenderResultDTO | None = None
    error: str | None = None
