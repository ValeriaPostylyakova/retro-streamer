from PIL import Image, ImageDraw


def render_board_to_image(board: list[list[int]], cell_size: int = 20) -> Image.Image:
    """Рисует матрицу поля с помощью Pillow."""
    grid_size = len(board)
    img_size = grid_size * cell_size

    # Создаем пустое изображение (RGB)
    img = Image.new("RGB", (img_size, img_size), "#222222")
    draw = ImageDraw.Draw(img)

    for r in range(grid_size):
        for c in range(grid_size):
            cell_type = board[r][c]

            x1 = c * cell_size
            y1 = r * cell_size
            x2 = x1 + cell_size - 1
            y2 = y1 + cell_size - 1

            if cell_type == 1:
                draw.rectangle([x1, y1, x2, y2], fill="#4CAF50")
            elif cell_type == 2:
                draw.rectangle([x1, y1, x2, y2], fill="#FF5252")
            else:
                draw.rectangle([x1, y1, x2, y2], outline="#333333", fill="#222222")

    return img
