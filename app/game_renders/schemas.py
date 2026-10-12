from pydantic import BaseModel, Field


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
    command_hash: str
    s3_key: str
