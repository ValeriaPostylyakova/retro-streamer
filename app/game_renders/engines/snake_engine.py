from PIL import Image, ImageDraw, ImageFont

from app.game_renders.engines import BaseGameRenderEngine
from app.game_renders.games import SnakeGame as InternalSnakeGame


class SnakeRenderEngine(BaseGameRenderEngine):
    def __init__(self, seed: int):
        super().__init__(seed)
        self.game = InternalSnakeGame()

    def step(self, command: str):
        board = self.game.step(command.lower())
        self.score = int(self.game.score)
        self.game_over = self.game.game_over
        self.steps_count = getattr(self.game, "steps_count", self.steps_count + 1)
        return board

    def render_board_to_image_snake(
        self,
        board: list[list[int]],
        cell_size: int = 20,
        draw_game_over: bool = False,
        score: int = 0,
    ) -> Image.Image:

        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0

        width = cols * cell_size
        height = rows * cell_size

        background_color = "#222222"
        outline_color = "#333333"

        img = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(img)

        color_snake = "#4CAF50"
        color_head = "#8BC34A"
        color_dead_body = "#555555"
        color_dead_head = "#F44336"
        color_food = "#FF5252"

        for r in range(rows):
            for c in range(cols):
                cell_type = board[r][c]
                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size - 1, y1 + cell_size - 1

                if cell_type == 1:
                    draw.rectangle([x1, y1, x2, y2], fill=color_snake)
                elif cell_type == 2:
                    draw.rectangle([x1, y1, x2, y2], fill=color_food)
                elif cell_type == 3:
                    draw.rectangle([x1, y1, x2, y2], fill=color_head)

                    draw.rectangle([x1 + 4, y1 + 4, x1 + 7, y1 + 7], fill="#000000")
                    draw.rectangle([x2 - 6, y1 + 4, x2 - 3, y1 + 7], fill="#000000")
                elif cell_type == 4:
                    draw.rectangle([x1, y1, x2, y2], fill=color_dead_head)
                    draw.line([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill="#FFFFFF", width=2)
                    draw.line([x2 - 3, y1 + 3, x1 + 3, y2 - 3], fill="#FFFFFF", width=2)
                elif cell_type == 5:
                    draw.rectangle([x1, y1, x2, y2], fill=color_dead_body)
                else:
                    draw.rectangle(
                        [x1, y1, x2, y2], outline=outline_color, fill=background_color
                    )

        if draw_game_over:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            overlay_draw.rectangle([0, 0, width, height], fill=(0, 0, 0, 178))

            try:
                font_title = ImageFont.load_default()
            except Exception:
                font_title = None

            text_1 = "GAME OVER"
            text_2 = f"SCORE: {score}"

            overlay_draw.text(
                (width // 2, height // 2 - 15),
                text_1,
                fill="#FF5252",
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

    def render_current_frame(self, draw_game_over: bool = False):
        return self.render_board_to_image_snake(
            self.game._get_board(),
            draw_game_over=draw_game_over,
            score=self.score if draw_game_over else 0,
        )

    def get_final_frames(self) -> list:
        frames = []
        if self.game_over:
            frames.append(self.render_current_frame(draw_game_over=False))
            game_over_frame = self.render_current_frame(draw_game_over=True)
            for _ in range(4):
                frames.append(game_over_frame)
        return frames
