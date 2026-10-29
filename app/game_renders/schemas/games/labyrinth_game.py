from typing import Literal

from pydantic import BaseModel, Field


class LabyrinthRenderRequest(BaseModel):
    commands: list[Literal["up", "down", "left", "right", "none"]] = Field(
        ...,
        max_length=150,
        min_length=2,
        examples=[["right", "none", "up", "left"]],
    )
    seed: int = 11
    game_name: Literal["labyrinth"]


class LabyrinthRules(BaseModel):
    field_size: int = 15
    max_commands: int = 150
    available_commands: list[str] = ["up", "down", "left", "right", "none"]


class LabyrinthInitialState(BaseModel):
    board: list[list[int]]
    player_position: list[int]
    enemies_positions: list[list[int]]
    coins_positions: list[list[int]]


class LabyrinthInfoResponse(BaseModel):
    game_name: Literal["labyrinth"] = "labyrinth"
    seed: int
    rules: LabyrinthRules
    initial_state: LabyrinthInitialState
