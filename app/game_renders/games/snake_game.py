import random


class SnakeGame:
    SIZE = 20
    DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}

    def __init__(self):
        self.snake = [(10, 10), (10, 9), (10, 8)]
        self.direction = "right"
        self.score = 0
        self.steps_count = 0
        self.game_over = False
        self.death_reason = None
        self.food = None
        self._spawn_food()

    def _spawn_food(self):
        free_cells = [
            (r, c)
            for r in range(self.SIZE)
            for c in range(self.SIZE)
            if (r, c) not in self.snake
        ]
        if free_cells:
            self.food = random.choice(free_cells)
        else:
            self.food = None
            self.game_over = True

    def _get_board(self):
        """Создаёт матрицу поля с учетом состояния игры."""
        board = [[0] * self.SIZE for _ in range(self.SIZE)]

        if not self.game_over:
            for r, c in self.snake[1:]:
                board[r][c] = 1
            hr, hc = self.snake[0]
            board[hr][hc] = 3
        else:
            for r, c in self.snake[1:]:
                board[r][c] = 5
            hr, hc = self.snake[0]
            board[hr][hc] = 4

        if self.food is not None:
            r, c = self.food
            board[r][c] = 2

        return board

    def step(self, command: str):
        if self.game_over:
            return self._get_board()

        if command not in self.DIRECTIONS:
            raise ValueError("Команда должна быть: 'up', 'down', 'left' или 'right'")

        self.steps_count += 1

        if command != self.OPPOSITE[self.direction]:
            self.direction = command

        dr, dc = self.DIRECTIONS[self.direction]
        head_r, head_c = self.snake[0]
        new_head = (head_r + dr, head_c + dc)
        r, c = new_head

        if not (0 <= r < self.SIZE and 0 <= c < self.SIZE):
            self.game_over = True
            self.death_reason = "wall"
            return self._get_board()

        eating = new_head == self.food
        body_to_check = self.snake if eating else self.snake[:-1]

        if new_head in body_to_check:
            self.game_over = True
            self.death_reason = "self"
            return self._get_board()

        self.snake.insert(0, new_head)

        if eating:
            self.score += 1
            self._spawn_food()
        else:
            self.snake.pop()

        return self._get_board()
