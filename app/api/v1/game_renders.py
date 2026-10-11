import io
import random

import imageio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.game_renders.games.snake_game import SnakeGame
from app.game_renders.schemas import (
    GameInfoResponse,
    GameInitialState,
    GameRenderRequest,
    GameRules,
)
from app.game_renders.utils.render_board_to_image import render_board_to_image

router = APIRouter()


@router.post("/play")
async def play_game_and_get_gif(request_data: GameRenderRequest):
    random.seed(request_data.seed)

    game = SnakeGame()
    frames = []

    initial_board = game._get_board()
    frames.append(render_board_to_image(initial_board))

    for command in request_data.commands:
        try:
            board = game.step(command.lower())
            frames.append(render_board_to_image(board))
            if game.game_over:
                break
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    gif_io = io.BytesIO()

    imageio.mimsave(gif_io, frames, format="GIF", fps=5, loop=0)
    gif_io.seek(0)

    return StreamingResponse(
        gif_io,
        media_type="image/gif",
        headers={"Content-Disposition": "inline; filename=result.gif"},
    )


@router.get("/info", response_model=GameInfoResponse)
async def get_game_info(
    seed: int = Query(42, description="Сид для фиксации случайного генератора еды"),
):

    random.seed(seed)
    game = SnakeGame()

    return GameInfoResponse(
        seed=seed,
        rules=GameRules(
            field_size=game.SIZE,
            max_commands=50,
            opposite_directions=game.OPPOSITE,
        ),
        initial_state=GameInitialState(
            snake_body=[list(cell) for cell in game.snake],
            current_direction=game.direction,
            food_position=list(game.food) if game.food else [],
        ),
    )
