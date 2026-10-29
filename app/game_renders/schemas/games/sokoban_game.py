from typing import Literal

from pydantic import BaseModel, Field


class SokobanRenderRequest(BaseModel):
    commands: list[Literal["up", "down", "left", "right"]] = Field(
        ...,
        max_length=150,
        min_length=2,
        examples=[["up", "right", "right", "down"]],
    )
    seed: int = 7
    game_name: Literal["sokoban"]


class SokobanRules(BaseModel):
    field_size: int = 10
    max_commands: int = 150
    available_commands: list[str] = ["up", "down", "left", "right"]


class SokobanInitialState(BaseModel):
    board: list[list[int]]
    player_position: list[int]
    boxes_positions: list[list[int]]
    targets_positions: list[list[int]]


class SokobanInfoResponse(BaseModel):
    game_name: Literal["sokoban"] = "sokoban"
    seed: int
    rules: SokobanRules
    initial_state: SokobanInitialState
