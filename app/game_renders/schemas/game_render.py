from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, RootModel

from app.schemas.base import BaseResponse

from .games.game_2048 import (
    Game2048InfoResponse,
    Game2048RenderRequest,
)
from .games.labyrinth_game import (
    LabyrinthInfoResponse,
    LabyrinthRenderRequest,
)
from .games.snake_game import (
    SnakeInfoResponse,
    SnakeRenderRequest,
)
from .games.sokoban_game import (
    SokobanInfoResponse,
    SokobanRenderRequest,
)

GameRequestUnion = Annotated[
    SnakeRenderRequest
    | SokobanRenderRequest
    | Game2048RenderRequest
    | LabyrinthRenderRequest,
    Field(discriminator="game_name"),
]


class RenderRequest(RootModel[GameRequestUnion]):
    pass


GameInfoUnion = Annotated[
    SnakeInfoResponse
    | SokobanInfoResponse
    | Game2048InfoResponse
    | LabyrinthInfoResponse,
    Field(discriminator="game_name"),
]


class GameInfoResponse(RootModel[GameInfoUnion]):
    pass


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
    steps_count: int
    render_id: UUID
    download_url: str

    expires_in: int = 300


class GameRenderResponseProcessing(BaseModel):
    status: str = RenderStatus.PENDING
    detail: str = "Обработка задачи с этими командами находится в процессе"


class GameRenderResultDTO(BaseModel):
    render_id: UUID
    score: int
    steps_count: int
    download_url: str


class TaskStatusResponse(BaseResponse):
    task_id: str
    status: str
    progress: int | None = None
    result: GameRenderResultDTO | None = None
    error: str | None = None
