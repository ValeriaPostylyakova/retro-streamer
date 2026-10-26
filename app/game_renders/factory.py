from app.game_renders.engines import (
    BaseGameRenderEngine,
    Game2048RenderEngine,
    LabyrinthRenderEngine,
    SnakeRenderEngine,
    SokobanRenderEngine,
)


class GameEngineFactory:
    _engines = {
        "snake": SnakeRenderEngine,
        "labyrinth": LabyrinthRenderEngine,
        "2048": Game2048RenderEngine,
        "sokoban": SokobanRenderEngine,
    }

    @classmethod
    def get_engine(cls, game_name: str, seed: int) -> BaseGameRenderEngine:
        engine_cls = cls._engines.get(game_name.lower())
        if not engine_cls:
            raise ValueError(f"Unknown game name: {game_name}")
        return engine_cls(seed=seed)
