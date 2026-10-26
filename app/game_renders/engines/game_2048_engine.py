import random

from PIL import Image, ImageDraw, ImageFont

from app.game_renders.engines import BaseGameRenderEngine
from app.game_renders.games.game_2048 import Game2048 as InternalGame2048


class Game2048RenderEngine(BaseGameRenderEngine):
    def __init__(self, seed: int):
        super().__init__(seed)
        random.seed(seed)
        self.game = InternalGame2048()

    def step(self, command: str) -> list[list[int]]:
        """Выполняет один сдвиг плиток, синхронизирует метрики и возвращает поле."""
        board = self.game.step(command.lower())

        self.score = int(self.game.score)
        self.game_over = self.game.game_over
        self.steps_count = getattr(self.game, "steps_count", self.steps_count + 1)

        return board

    def render_board_to_image_2048(
        self,
        board: list[list[int]],
        cell_size: int = 60,
        draw_game_over: bool = False,
        score: int = 0,
    ) -> Image.Image:
        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0

        width = cols * cell_size
        height = rows * cell_size

        background_color = "#BBADA0"
        img = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(img)

        tile_colors = {
            0: ("#CDC1B4", "#776E65"),
            2: ("#EEE4DA", "#776E65"),
            4: ("#EDE0C8", "#776E65"),
            8: ("#F2B179", "#F9F6F2"),
            16: ("#F59563", "#F9F6F2"),
            32: ("#F67C5F", "#F9F6F2"),
            64: ("#F65E3B", "#F9F6F2"),
            128: ("#EDCF72", "#F9F6F2"),
            256: ("#EDCC61", "#F9F6F2"),
            512: ("#EDC850", "#F9F6F2"),
            1024: ("#EDC53F", "#F9F6F2"),
            2048: ("#EDC22E", "#F9F6F2"),
        }
        default_tile_color = ("#3C3A32", "#F9F6F2")

        try:
            font_text = ImageFont.load_default()
        except Exception:
            font_text = None

        for r in range(rows):
            for c in range(cols):
                value = board[r][c]

                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size - 1, y1 + cell_size - 1

                pad = 4
                tile_x1, tile_y1 = x1 + pad, y1 + pad
                tile_x2, tile_y2 = x2 - pad, y2 - pad

                bg_hex, text_hex = tile_colors.get(value, default_tile_color)

                draw.rectangle([tile_x1, tile_y1, tile_x2, tile_y2], fill=bg_hex)

                if value != 0:
                    center_x = (tile_x1 + tile_x2) // 2
                    center_y = (tile_y1 + tile_y2) // 2

                    draw.text(
                        (center_x, center_y),
                        str(value),
                        fill=text_hex,
                        anchor="mm",
                        font=font_text,
                    )

        if draw_game_over:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            overlay_draw.rectangle([0, 0, width, height], fill=(238, 228, 218, 180))

            try:
                font_title = ImageFont.load_default()
            except Exception:
                font_title = None

            text_1 = "GAME OVER"
            text_2 = f"SCORE: {score}"

            overlay_draw.text(
                (width // 2, height // 2 - 12),
                text_1,
                fill="#776E65",
                anchor="mm",
                font=font_title,
            )
            overlay_draw.text(
                (width // 2, height // 2 + 12),
                text_2,
                fill="#776E65",
                anchor="mm",
                font=font_title,
            )

            img.paste(overlay, (0, 0), overlay)

        return img

    def render_current_frame(self, draw_game_over: bool = False) -> Image.Image:
        return self.render_board_to_image_2048(
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
