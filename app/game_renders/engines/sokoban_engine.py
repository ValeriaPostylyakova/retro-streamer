import random

from PIL import Image, ImageDraw, ImageFont

from app.game_renders.engines import BaseGameRenderEngine
from app.game_renders.games.sokoban_game import SokobanGame as InternalSokobanGame


class SokobanRenderEngine(BaseGameRenderEngine):
    def __init__(self, seed: int):
        super().__init__(seed)
        random.seed(seed)
        self.game = InternalSokobanGame()

    def step(self, command: str):
        board = self.game.step(command.lower())

        self.score = int(self.game.score)
        self.game_over = self.game.game_over
        self.steps_count = getattr(self.game, "steps_count", self.steps_count + 1)

        return board

    def render_board_to_image_sokoban(
        self,
        board: list[list[int]],
        cell_size: int = 24,
        draw_game_over: bool = False,
        score: int = 0,
    ) -> Image.Image:
        """Отрисовывает матрицу Сокобана (10x10) в PIL Image."""
        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0

        width = cols * cell_size
        height = rows * cell_size

        background_color = "#2E3440"  # Современный темно-серый (Nord фреймворк)
        outline_color = "#3B4252"  # Едва заметная сетка пола

        img = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(img)

        color_wall = "#4C566A"  # Крепкая каменная стена
        color_target = "#EBCB8B"  # Золотистая точка-цель
        color_box = "#D08770"  # Обычный деревянный ящик (терракотовый)
        color_box_on_target = "#A3BE8C"  # Ящик на месте! (Изумрудно-зеленый)
        color_player = "#81A1C1"  # Игрок (Стильный голубой)
        color_player_on_target = "#88C0D0"  # Игрок наступил на цель

        for r in range(rows):
            for c in range(cols):
                cell_type = board[r][c]

                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size - 1, y1 + cell_size - 1

                if cell_type == 0:
                    draw.rectangle(
                        [x1, y1, x2, y2], outline=outline_color, fill=background_color
                    )

                elif cell_type == 1:
                    draw.rectangle([x1, y1, x2, y2], fill=color_wall, outline="#434C5E")

                elif cell_type == 2:
                    draw.rectangle(
                        [x1, y1, x2, y2], outline=outline_color, fill=background_color
                    )
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    r_dot = cell_size // 4
                    draw.ellipse(
                        [cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot],
                        fill=color_target,
                    )

                elif cell_type == 3:
                    draw.rectangle([x1, y1, x2, y2], fill=color_box, outline="#BF616A")
                    draw.rectangle(
                        [x1 + 4, y1 + 4, x2 - 4, y2 - 4], outline="#BF616A", width=1
                    )

                elif cell_type == 4:
                    draw.rectangle(
                        [x1, y1, x2, y2], fill=color_box_on_target, outline="#8FBCBB"
                    )
                    draw.line([x1 + 4, y1 + 4, x2 - 4, y2 - 4], fill="#8FBCBB", width=2)
                    draw.line([x2 - 4, y1 + 4, x1 + 4, y2 - 4], fill="#8FBCBB", width=2)

                elif cell_type == 5:
                    draw.rectangle(
                        [x1, y1, x2, y2], outline=outline_color, fill=background_color
                    )
                    draw.ellipse([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill=color_player)

                elif cell_type == 6:
                    draw.rectangle(
                        [x1, y1, x2, y2], outline=outline_color, fill=background_color
                    )
                    draw.ellipse(
                        [x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill=color_player_on_target
                    )

        if draw_game_over:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([0, 0, width, height], fill=(0, 0, 0, 180))

            try:
                font_title = ImageFont.load_default()
            except Exception:
                font_title = None

            text_1 = "LEVEL SOLVED!"
            text_2 = f"SCORE: {score}"

            overlay_draw.text(
                (width // 2, height // 2 - 15),
                text_1,
                fill="#A3BE8C",
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
        return self.render_board_to_image_sokoban(
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
