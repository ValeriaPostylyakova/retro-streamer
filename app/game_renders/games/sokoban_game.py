class SokobanGame:
    SIZE = 10
    DIRECTIONS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    def __init__(self):
        # Фиксированная карта лабиринта
        self.walls = {
            (r, c)
            for r in range(self.SIZE)
            for c in range(self.SIZE)
            if r == 0 or r == self.SIZE - 1 or c == 0 or c == self.SIZE - 1
        }

        # Внутренние стены лабиринта
        self.walls.update(
            {
                (2, 2),
                (2, 3),
                (2, 6),
                (2, 7),
                (3, 2),
                (3, 7),
                (4, 4),
                (4, 5),
                (5, 2),
                (5, 7),
                (6, 2),
                (6, 3),
                (6, 6),
                (6, 7),
            }
        )

        self.player = (1, 1)
        self.boxes = {(3, 3), (3, 5), (5, 5)}
        self.targets = {(1, 8), (7, 3), (8, 8)}

        self.score = 0
        self.steps_count = 0
        self.game_over = False

    def _get_board(self):
        """Создаёт матрицу поля с учетом состояния игры."""
        board = [[0] * self.SIZE for _ in range(self.SIZE)]

        # Стены лабиринта
        for r, c in self.walls:
            board[r][c] = 1

        # Целевые точки
        for r, c in self.targets:
            board[r][c] = 2

        # Ящики и ящики на целевых точках
        for r, c in self.boxes:
            if (r, c) in self.targets:
                board[r][c] = 4
            else:
                board[r][c] = 3

        # Игрок и игрок на целевой точке
        r, c = self.player
        if (r, c) in self.targets:
            board[r][c] = 6
        else:
            board[r][c] = 5

        return board

    def step(self, command: str):
        if self.game_over:
            return self._get_board()

        if command not in self.DIRECTIONS:
            raise ValueError("Команда должна быть: 'up', 'down', 'left' или 'right'")

        self.steps_count += 1

        dr, dc = self.DIRECTIONS[command]
        player_r, player_c = self.player
        new_player = (player_r + dr, player_c + dc)

        # Проверка границ поля и стен
        if (
            not (0 <= new_player[0] < self.SIZE and 0 <= new_player[1] < self.SIZE)
            or new_player in self.walls
        ):
            return self._get_board()

        # Если впереди ящик, проверяем возможность его толкнуть
        if new_player in self.boxes:
            box_r, box_c = new_player
            new_box = (box_r + dr, box_c + dc)

            # Нельзя толкать ящик в стену, за границу или в другой ящик
            if (
                not (0 <= new_box[0] < self.SIZE and 0 <= new_box[1] < self.SIZE)
                or new_box in self.walls
                or new_box in self.boxes
            ):
                return self._get_board()

            # Перемещаем ящик
            was_on_target = new_player in self.targets
            will_be_on_target = new_box in self.targets

            self.boxes.remove(new_player)
            self.boxes.add(new_box)

            # Начисляем или снимаем очки за занятые целевые точки
            if will_be_on_target and not was_on_target:
                self.score += 100
            elif was_on_target and not will_be_on_target:
                self.score -= 100

        # Перемещаем игрока
        self.player = new_player

        # Проверяем условие победы
        if self.boxes == self.targets:
            self.game_over = True

        return self._get_board()
