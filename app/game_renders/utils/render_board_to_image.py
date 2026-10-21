from PIL import Image, ImageDraw


def render_board_to_image(
    board: list[list[int]], game_name: str = "snake", cell_size: int = 20
) -> Image.Image:

    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    width = cols * cell_size
    height = rows * cell_size

    background_color = "#222222"
    outline_color = "#333333"

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    if game_name == "tetris":
        color_1 = "#2196F3"
        color_2 = "#FF9800"
    else:
        color_1 = "#4CAF50"
        color_2 = "#FF5252"

    for r in range(rows):
        for c in range(cols):
            cell_type = board[r][c]

            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size - 1
            y2 = y1 + cell_size - 1

            if cell_type == 1:
                draw.rectangle([x1, y1, x2, y2], fill=color_1)
            elif cell_type == 2:
                draw.rectangle([x1, y1, x2, y2], fill=color_2)
            else:
                draw.rectangle(
                    [x1, y1, x2, y2], outline=outline_color, fill=background_color
                )

    return img
