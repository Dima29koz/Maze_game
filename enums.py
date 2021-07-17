from enum import Enum, auto


class Directions(Enum):
    mouth = 0
    top = 1
    right = 2
    bottom = 3
    left = 4


class Actions(Enum):
    skip = auto()
    move = auto()
    shoot_bow = auto()
    throw_bomb = auto()

