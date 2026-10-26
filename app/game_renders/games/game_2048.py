import random


class Game2048:
    SIZE = 4
    DIRECTIONS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    def __init__(self):
        self.board = [[0] * self.SIZE for _ in range(self.SIZE)]
        self.score = 0
        self.steps_count = 0
        self.game_over = False

        self._spawn_tile()
        self._spawn_tile()

    def _spawn_tile(self):
        """Создаёт случайную плитку на свободной клетке."""
        free_cells = [
            (r, c)
            for r in range(self.SIZE)
            for c in range(self.SIZE)
            if self.board[r][c] == 0
        ]

        if free_cells:
            r, c = random.choice(free_cells)
            self.board[r][c] = random.choices([2, 4], weights=[90, 10])[0]
        else:
            self._check_game_over()

    def _get_board(self):
        """Возвращает копию текущей матрицы игрового поля."""
        return [row[:] for row in self.board]

    def _merge_line(self, line):
        """Сдвигает ненулевые плитки влево и объединяет одинаковые."""
        tiles = [value for value in line if value != 0]
        merged = []
        i = 0

        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                value = tiles[i] * 2
                merged.append(value)
                self.score += value
                i += 2
            else:
                merged.append(tiles[i])
                i += 1

        merged.extend([0] * (self.SIZE - len(merged)))
        return merged

    def _move(self, command):
        """Выполняет сдвиг плиток в указанном направлении."""
        old_board = self._get_board()

        if command == "left":
            for r in range(self.SIZE):
                self.board[r] = self._merge_line(self.board[r])

        elif command == "right":
            for r in range(self.SIZE):
                reversed_line = self.board[r][::-1]
                merged = self._merge_line(reversed_line)
                self.board[r] = merged[::-1]

        elif command == "up":
            for c in range(self.SIZE):
                line = [self.board[r][c] for r in range(self.SIZE)]
                merged = self._merge_line(line)

                for r in range(self.SIZE):
                    self.board[r][c] = merged[r]

        elif command == "down":
            for c in range(self.SIZE):
                line = [self.board[r][c] for r in range(self.SIZE - 1, -1, -1)]
                merged = self._merge_line(line)

                for i, r in enumerate(range(self.SIZE - 1, -1, -1)):
                    self.board[r][c] = merged[i]

        return self.board != old_board

    def _can_move(self):
        """Проверяет, существует ли хотя бы один допустимый ход."""
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                value = self.board[r][c]

                if value == 0:
                    return True

                if r + 1 < self.SIZE and self.board[r + 1][c] == value:
                    return True

                if c + 1 < self.SIZE and self.board[r][c + 1] == value:
                    return True

        return False

    def _check_game_over(self):
        """Проверяет, закончилась ли игра."""
        if not self._can_move():
            self.game_over = True

    def step(self, command: str):
        if self.game_over:
            return self._get_board()

        if command not in self.DIRECTIONS:
            raise ValueError("Команда должна быть: 'up', 'down', 'left' или 'right'")

        changed = self._move(command)

        if changed:
            self.steps_count += 1
            self._spawn_tile()

        self._check_game_over()

        return self._get_board()
