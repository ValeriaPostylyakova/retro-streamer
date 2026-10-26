from typing import Literal

from pydantic import BaseModel, Field


class SnakeRenderRequest(BaseModel):
    commands: list[Literal["up", "down", "left", "right"]] = Field(
        ...,
        max_length=250,
        min_length=2,
        examples=[["up", "down", "left", "right"]],
    )
    seed: int = 5
    game_name: Literal["snake"] = "snake"


class SnakeRules(BaseModel):
    field_size: int = 20
    max_commands: int = 250
    opposite_directions: dict[str, str] = {
        "up": "down",
        "down": "up",
        "left": "right",
        "right": "left",
    }
    available_commands: list[str] = ["up", "down", "left", "right"]


class SnakeInitialState(BaseModel):
    snake_body: list[list[int]]
    current_direction: str
    food_position: list[int]


class SnakeInfoResponse(BaseModel):
    game_name: Literal["snake"] = "snake"
    seed: int
    rules: SnakeRules
    initial_state: SnakeInitialState
