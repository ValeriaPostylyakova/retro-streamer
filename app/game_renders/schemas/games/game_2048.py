from typing import Literal

from pydantic import BaseModel, Field


class Game2048RenderRequest(BaseModel):
    commands: list[Literal["up", "down", "left", "right"]] = Field(
        ...,
        max_length=500,
        min_length=2,
        examples=[["left", "up", "right", "down"]],
    )
    seed: int = 2048
    game_name: Literal["2048"]


class Game2048Rules(BaseModel):
    field_size: int = 4
    max_commands: int = 500
    available_commands: list[str] = ["up", "down", "left", "right"]


class Game2048InitialState(BaseModel):
    board: list[list[int]]


class Game2048InfoResponse(BaseModel):
    game_name: Literal["2048"] = "2048"
    seed: int
    rules: Game2048Rules
    initial_state: Game2048InitialState
