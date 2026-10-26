import random

from PIL import Image, ImageDraw, ImageFont

from app.game_renders.engines import BaseGameRenderEngine
from app.game_renders.games.labyrinth_game import LabyrinthGame as InternalLabyrinthGame


class LabyrinthRenderEngine(BaseGameRenderEngine):
    def __init__(self, seed: int):
        super().__init__(seed)
        random.seed(seed)
        self.game = InternalLabyrinthGame()

    def step(self, command: str) -> list[list[int]]:
        """Выполняет один шаг игрока и автоматический ход привидений, обновляет метрики."""
        board = self.game.step(command.lower())

        self.score = int(self.game.score)
        self.game_over = self.game.game_over
        self.steps_count = getattr(self.game, "steps_count", self.steps_count + 1)

        return board

    def render_board_to_image_labyrinth(
        self,
        board: list[list[int]],
        cell_size: int = 20,
        draw_game_over: bool = False,
        score: int = 0,
    ) -> Image.Image:
        """Отрисовывает матрицу Лабиринта (15x15) в PIL Image в неоновом аркадном стиле."""
        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0

        width = cols * cell_size
        height = rows * cell_size

        background_color = "#0B0C10"
        img = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(img)

        color_wall = "#1F2833"  # Технологичный темно-синий для стен
        color_wall_edge = "#45A29E"  # Неоновый бирюзовый контур стен
        color_coin = "#FFD700"  # Золотые монеты
        color_exit = "#66BB6A"  # Ярко-зеленый выход
        color_player = "#FBC02D"  # Желтый Пакман-герой
        color_enemy = "#EF5350"  # Красные привидения
        color_dead_player = "#D32F2F"  # Цвет погибшего игрока

        for r in range(rows):
            for c in range(cols):
                cell_type = board[r][c]

                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size - 1, y1 + cell_size - 1

                if cell_type == 1:
                    draw.rectangle(
                        [x1, y1, x2, y2], fill=color_wall, outline=color_wall_edge
                    )

                elif cell_type == 2:
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    r_coin = cell_size // 5
                    draw.ellipse(
                        [cx - r_coin, cy - r_coin, cx + r_coin, cy + r_coin],
                        fill=color_coin,
                    )

                elif cell_type == 3:
                    draw.rectangle(
                        [x1 + 2, y1 + 2, x2 - 2, y2 - 2],
                        fill=color_exit,
                        outline="#A5D6A7",
                    )

                elif cell_type == 4:
                    draw.ellipse([x1 + 2, y1 + 2, x2 - 2, y2 - 2], fill=color_player)

                elif cell_type == 5:
                    draw.ellipse([x1 + 1, y1 + 1, x2 - 1, y2 - 3], fill=color_enemy)
                    draw.rectangle(
                        [x1 + 1, (y1 + y2) // 2, x2 - 1, y2 - 1], fill=color_enemy
                    )

                elif cell_type == 6:
                    draw.rectangle([x1, y1, x2, y2], fill=color_dead_player)
                    draw.line([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill="#FFFFFF", width=2)
                    draw.line([x2 - 3, y1 + 3, x1 + 3, y2 - 3], fill="#FFFFFF", width=2)

        if draw_game_over:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([0, 0, width, height], fill=(0, 0, 0, 185))

            try:
                font_title = ImageFont.load_default()
            except Exception:
                font_title = None

            is_victory = getattr(self.game, "death_reason", None) is None

            text_1 = "VICTORY!" if is_victory else "GAME OVER"
            text_color = color_exit if is_victory else "#FF5252"
            text_2 = f"COINS: {score}"

            overlay_draw.text(
                (width // 2, height // 2 - 15),
                text_1,
                fill=text_color,
                anchor="mm",
                font=font_title,
            )
            overlay_draw.text(
                (width // 2, height // 2 + 10),
                text_2,
                fill="#FFFFFF",
                anchor="mm",
                font=font_title,
            )

            img.paste(overlay, (0, 0), overlay)

        return img

    def render_current_frame(self, draw_game_over: bool = False) -> Image.Image:
        return self.render_board_to_image_labyrinth(
            self.game._get_board(),
            draw_game_over=draw_game_over,
            score=self.score if draw_game_over else 0,
        )

    def get_final_frames(self) -> list[Image.Image]:
        frames = []
        if self.game_over:
            frames.append(self.render_current_frame(draw_game_over=False))

            game_over_frame = self.render_current_frame(draw_game_over=True)
            for _ in range(4):
                frames.append(game_over_frame)
        return frames
