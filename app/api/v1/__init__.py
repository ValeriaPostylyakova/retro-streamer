from fastapi import APIRouter

from app.api.v1 import auth, game_renders, game_renders_ws, leaderboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(game_renders.router, prefix="/game", tags=["game"])
api_router.include_router(game_renders_ws.router, prefix="/game", tags=["game_ws"])
api_router.include_router(
    leaderboard.router, prefix="/leaderboard", tags=["leaderboard"]
)
