from enum import Enum, auto


class Directions(Enum):
    """
    describes directions

    :cvar top: direction `top`
    :cvar right: direction `right`
    :cvar bottom: direction `bottom`
    :cvar left: direction `left`
    """
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


# noinspection PyArgumentList
class Actions(Enum):
    """
    describes actions

    :cvar skip: action `skip`
    :cvar move: action `move`
    :cvar shoot_bow: action `shoot_bow`
    :cvar throw_bomb: action `throw_bomb`
    :cvar swap_treasure: action `swap_treasure`
    :cvar info: action `info`
    """
    skip = auto()
    move = auto()
    shoot_bow = auto()
    throw_bomb = auto()
    swap_treasure = auto()
    info = auto()


# noinspection PyArgumentList
class TreasureTypes(Enum):
    """
    describes treasure types

    :cvar very: treasure type `very`
    :cvar spurious: treasure type `spurious`
    :cvar mined: treasure type `mined`
    """
    very = auto()
    spurious = auto()
    mined = auto()
