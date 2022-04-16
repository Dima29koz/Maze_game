from enum import Enum, auto


class Directions(Enum):
    """
    describes directions

    :param top: direction `top`
    :param right: direction `right`
    :param bottom: direction `bottom`
    :param left: direction `left`
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

    def calc(self, x: int, y: int) -> tuple[int, int]:
        """return changed coordinates by direction"""
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
    """
    describes actions

    :param skip: action `skip`
    :param move: action `move`
    :param shoot_bow: action `shoot_bow`
    :param throw_bomb: action `throw_bomb`
    :param swap_treasure: action `swap_treasure`
    :param info: action `info`
    """
    skip = auto()
    move = auto()
    shoot_bow = auto()
    throw_bomb = auto()
    swap_treasure = auto()
    info = auto()


class TreasureTypes(Enum):
    """
    describes treasure types

    :param very: treasure type `very`
    :param spurious: treasure type `spurious`
    :param mined: treasure type `mined`
    """
    very = auto()
    spurious = auto()
    mined = auto()
