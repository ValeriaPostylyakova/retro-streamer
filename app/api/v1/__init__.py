from fastapi import APIRouter

from app.api.v1 import auth, game_renders

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["users"])
api_router.include_router(game_renders.router, prefix="/game", tags=["game"])
