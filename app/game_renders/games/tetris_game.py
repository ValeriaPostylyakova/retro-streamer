import random


class TetrisGame:
    WIDTH: int = 10
    HEIGHT: int = 20

    # Семь стандартных фигур.
    SHAPES: list[list[list[int]]] = [
        # I
        [[1, 1, 1, 1]],
        # O
        [[1, 1], [1, 1]],
        # T
        [[0, 1, 0], [1, 1, 1]],
        # S
        [[0, 1, 1], [1, 1, 0]],
        # Z
        [[1, 1, 0], [0, 1, 1]],
        # J
        [[1, 0, 0], [1, 1, 1]],
        # L
        [[0, 0, 1], [1, 1, 1]],
    ]

    def __init__(self) -> None:
        # 0 — пустая клетка, 1 — зафиксированный блок.
        self.board: list[list[int]] = [[0] * self.WIDTH for _ in range(self.HEIGHT)]

        self.score: int = 0
        self.lines_cleared: int = 0
        self.game_over: bool = False

        self.piece: list[list[int]] | None = None
        self.x: int = 0
        self.y: int = 0

        self._spawn_piece()

    def _spawn_piece(self) -> None:
        """Создаёт новую случайную фигуру."""
        shape = random.choice(self.SHAPES)
        self.piece = [row[:] for row in shape]

        piece_width = len(self.piece[0])
        self.x = (self.WIDTH - piece_width) // 2
        self.y = 0

        if self._collides(self.x, self.y, self.piece):
            self.game_over = True

    def _collides(self, x: int, y: int, piece: list[list[int]]) -> bool:
        """Проверяет столкновения со стенами, дном и блоками."""
        for row_idx, row in enumerate(piece):
            for col_idx, cell in enumerate(row):
                if cell == 0:
                    continue

                board_x = x + col_idx
                board_y = y + row_idx

                # Левая и правая стены, дно.
                if board_x < 0 or board_x >= self.WIDTH or board_y >= self.HEIGHT:
                    return True

                # Выше поля блоки временно разрешены.
                if board_y < 0:
                    continue

                if self.board[board_y][board_x] == 1:
                    return True

        return False

    def _rotate(self, piece: list[list[int]]) -> list[list[int]]:
        """Поворачивает фигуру на 90 градусов по часовой стрелке."""
        return [list(row) for row in zip(*piece[::-1])]

    def _clear_lines(self) -> None:
        """Удаляет заполненные строки."""
        remaining: list[list[int]] = [
            row for row in self.board if not all(cell == 1 for cell in row)
        ]

        cleared = self.HEIGHT - len(remaining)

        if cleared == 0:
            return

        empty_rows: list[list[int]] = [[0] * self.WIDTH for _ in range(cleared)]

        self.board = empty_rows + remaining
        self.lines_cleared += cleared

        # Очки за 1, 2, 3 или 4 линии.
        points: dict[int, int] = {
            1: 100,
            2: 300,
            3: 500,
            4: 800,
        }
        self.score += points.get(cleared, cleared * 200)

    def _lock_piece(self) -> None:
        """Фиксирует активную фигуру и запускает следующую."""
        if self.piece is None:
            return

        for row_idx, row in enumerate(self.piece):
            for col_idx, cell in enumerate(row):
                if cell == 0:
                    continue

                board_x = self.x + col_idx
                board_y = self.y + row_idx

                if 0 <= board_y < self.HEIGHT:
                    self.board[board_y][board_x] = 1

        self._clear_lines()
        self._spawn_piece()

    def _move_down(self) -> None:
        """Опускает фигуру на одну клетку."""
        if self.piece is None:
            return

        if not self._collides(self.x, self.y + 1, self.piece):
            self.y += 1
        else:
            self._lock_piece()

    def _hard_drop(self) -> None:
        """Опускает фигуру до препятствия."""
        if self.piece is None:
            return

        while not self._collides(self.x, self.y + 1, self.piece):
            self.y += 1

        self._lock_piece()

    def _get_board(self) -> list[list[int]]:
        """Возвращает копию поля с активной фигурой."""
        result: list[list[int]] = [row[:] for row in self.board]

        if self.piece is None:
            return result

        for row_idx, row in enumerate(self.piece):
            for col_idx, cell in enumerate(row):
                if cell == 0:
                    continue

                board_x = self.x + col_idx
                board_y = self.y + row_idx

                if 0 <= board_x < self.WIDTH and 0 <= board_y < self.HEIGHT:
                    result[board_y][board_x] = 2

        return result

    def step(self, command: str) -> list[list[int]]:
        """
        Выполняет один игровой ход и возвращает поле 20x10.

        Команды:
            left   — движение влево
            right  — движение вправо
            rotate — вращение по часовой стрелке
            drop   — мгновенное падение
            none   — падение на одну клетку

        Значения матрицы:
            0 — пустая клетка
            1 — зафиксированный блок
            2 — активная фигура
        """
        valid_commands = {"left", "right", "rotate", "drop", "none"}

        if command not in valid_commands:
            raise ValueError(
                "Недопустимая команда. Используйте: "
                "'left', 'right', 'rotate', 'drop', 'none'."
            )

        if self.game_over:
            return self._get_board()

        if self.piece is None:
            return self._get_board()

        if command == "left":
            if not self._collides(self.x - 1, self.y, self.piece):
                self.x -= 1

        elif command == "right":
            if not self._collides(self.x + 1, self.y, self.piece):
                self.x += 1

        elif command == "rotate":
            rotated = self._rotate(self.piece)

            if not self._collides(self.x, self.y, rotated):
                self.piece = rotated

        elif command == "drop":
            self._hard_drop()

        elif command == "none":
            self._move_down()

        return self._get_board()
