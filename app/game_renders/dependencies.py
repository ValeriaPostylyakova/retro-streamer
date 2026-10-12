from app.game_renders.services import GameRenderService


def get_game_render_service() -> GameRenderService:
    return GameRenderService()
