from enum import Enum, IntEnum


class AllowedGames(str, Enum):
    snake = "snake"


class AllowedSeeds(IntEnum):
    five = 5
    forty_two = 42
    eighty_eight = 88
