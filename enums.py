from enum import Enum, auto


class Directions(Enum):
    top = 1
    right = 2
    bottom = 3
    left = 4

    def __neg__(self):
        if self is Directions.top:
            return Directions.bottom
        if self is Directions.bottom:
            return Directions.top
        if self is Directions.left:
            return Directions.right
        if self is Directions.right:
            return Directions.left
        if self is Directions.mouth:
            return Directions.mouth

    def calc(self, x, y):
        if self is Directions.top:
            y -= 1
        elif self is Directions.bottom:
            y += 1
        elif self is Directions.left:
            x -= 1
        elif self is Directions.right:
            x += 1
        return x, y


class Actions(Enum):
    skip = auto()
    move = auto()
    shoot_bow = auto()
    throw_bomb = auto()
    swap_treasure = auto()
    hurted = auto()  # for tests


class TreasureTypes(Enum):
    very = auto()
    spurious = auto()
    mined = auto()
