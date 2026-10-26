from abc import ABC, abstractmethod
from typing import Any


class BaseGameRenderEngine(ABC):
    def __init__(self, seed: int):
        self.seed = seed
        self.score: int = 0
        self.steps_count: int = 0
        self.game_over: bool = False

    @abstractmethod
    def step(self, command: str) -> Any:
        """Выполняет один шаг игры на основе команды."""

    @abstractmethod
    def render_current_frame(self, draw_game_over: bool = False) -> Any:
        """Возвращает отрендеренный кадр (например, PIL.Image)."""

    def get_initial_frames(self) -> list[Any]:
        """Возвращает стартовые кадры (по умолчанию один начальный кадр)."""
        return [self.render_current_frame(draw_game_over=False)]

    def get_final_frames(self) -> list[Any]:
        """Возвращает кадры завершения игры (например, анимация Game Over)."""
        return []
