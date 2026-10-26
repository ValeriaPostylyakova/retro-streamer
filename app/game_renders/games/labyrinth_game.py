class LabyrinthGame:
    SIZE = 15
    DIRECTIONS = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
        "none": (0, 0),
    }

    def __init__(self):
        self.walls = {
            (r, c)
            for r in range(self.SIZE)
            for c in range(self.SIZE)
            if r == 0 or r == self.SIZE - 1 or c == 0 or c == self.SIZE - 1
        }

        # Внутренние стены
        self.walls.update(
            {
                (2, 2),
                (2, 3),
                (2, 5),
                (2, 6),
                (2, 9),
                (2, 10),
                (3, 5),
                (3, 9),
                (4, 1),
                (4, 2),
                (4, 3),
                (4, 7),
                (4, 10),
                (4, 11),
                (5, 7),
                (5, 11),
                (6, 3),
                (6, 4),
                (6, 7),
                (6, 8),
                (6, 11),
                (7, 3),
                (7, 8),
                (8, 1),
                (8, 2),
                (8, 6),
                (8, 7),
                (8, 8),
                (8, 12),
                (9, 6),
                (9, 12),
                (10, 3),
                (10, 4),
                (10, 9),
                (10, 10),
                (10, 12),
                (11, 3),
                (11, 9),
                (12, 5),
                (12, 6),
                (12, 7),
                (12, 10),
                (12, 11),
            }
        )

        # Стартовая позиция игрока
        self.player = (1, 1)

        # Точка выхода
        self.exit = (13, 13)

        # Монеты
        self.coins = {
            (1, 4),
            (1, 8),
            (1, 12),
            (3, 2),
            (3, 7),
            (3, 12),
            (5, 4),
            (5, 9),
            (5, 13),
            (7, 1),
            (7, 6),
            (7, 11),
            (9, 3),
            (9, 8),
            (9, 13),
            (11, 1),
            (11, 6),
            (11, 12),
            (13, 3),
            (13, 8),
        }

        # Три врага
        self.enemies = [
            (1, 13),
            (7, 13),
            (13, 1),
        ]

        self.score = 0
        self.steps_count = 0
        self.game_over = False
        self.death_reason = None

    def _get_board(self):
        """Создаёт матрицу поля с учетом состояния игры."""
        board = [[0] * self.SIZE for _ in range(self.SIZE)]

        # Стены
        for r, c in self.walls:
            board[r][c] = 1

        # Монеты
        for r, c in self.coins:
            board[r][c] = 2

        # Выход
        er, ec = self.exit
        board[er][ec] = 3

        # Враги
        for r, c in self.enemies:
            board[r][c] = 5

        # Игрок
        pr, pc = self.player
        if self.game_over and self.death_reason == "enemy":
            board[pr][pc] = 6
        else:
            board[pr][pc] = 4

        return board

    def _move_enemies(self):
        """Перемещает каждого врага на один шаг в сторону игрока."""
        new_enemies = []

        for enemy in self.enemies:
            er, ec = enemy
            pr, pc = self.player

            # Если враг уже находится на игроке
            if enemy == self.player:
                new_enemies.append(enemy)
                continue

            # Предпочитаем горизонтальный или вертикальный шаг,
            # который сокращает расстояние до игрока.
            candidates = []

            if ec < pc:
                candidates.append((er, ec + 1))
            elif ec > pc:
                candidates.append((er, ec - 1))

            if er < pr:
                candidates.append((er + 1, ec))
            elif er > pr:
                candidates.append((er - 1, ec))

            # Если первый путь заблокирован стеной,
            # пробуем альтернативное направление.
            valid_moves = [
                pos
                for pos in candidates
                if pos not in self.walls
                and 0 <= pos[0] < self.SIZE
                and 0 <= pos[1] < self.SIZE
            ]

            if valid_moves:
                new_enemies.append(valid_moves[0])
            else:
                new_enemies.append(enemy)

        self.enemies = new_enemies

    def step(self, command: str):
        if self.game_over:
            return self._get_board()

        if command not in self.DIRECTIONS:
            raise ValueError(
                "Команда должна быть: 'up', 'down', 'left', 'right' или 'none'"
            )

        self.steps_count += 1

        # Движение игрока
        dr, dc = self.DIRECTIONS[command]
        pr, pc = self.player
        new_player = (pr + dr, pc + dc)

        if (
            0 <= new_player[0] < self.SIZE
            and 0 <= new_player[1] < self.SIZE
            and new_player not in self.walls
        ):
            self.player = new_player

        # Проверка сбора монеты
        if self.player in self.coins:
            self.coins.remove(self.player)
            self.score += 1

        # Проверка достижения выхода
        if self.player == self.exit:
            self.game_over = True
            self.death_reason = None
            return self._get_board()

        # Проверка столкновения с врагом после хода игрока
        if self.player in self.enemies:
            self.game_over = True
            self.death_reason = "enemy"
            return self._get_board()

        # Автоматический ход врагов
        self._move_enemies()

        # Проверка столкновения после движения врагов
        if self.player in self.enemies:
            self.game_over = True
            self.death_reason = "enemy"

        return self._get_board()
