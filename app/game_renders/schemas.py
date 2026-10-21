from enum import Enum
from uuid import UUID

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
    seed: int = 5


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
