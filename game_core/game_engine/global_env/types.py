from .enums import Directions


class LevelPosition:
    __slots__ = 'level', 'sub_level', 'dimension'

    def __init__(self, level: int, sub_level: int, dimension: int = 0):
        """

        :param level: game level number
        :param sub_level: game sub level number
        :param dimension: dimension of a level
        """
        self.level = level
        self.sub_level = sub_level
        self.dimension = dimension

    def to_dict(self):
        return {
            'level': self.level,
            'sub_level': self.sub_level,
            'dimension': self.dimension,
        }

    def __eq__(self, other: 'LevelPosition'):
        return self.level == other.level and self.sub_level == other.sub_level and self.dimension == other.dimension


class Position:
    """
    describes the position of an object

    :ivar x: x position
    :ivar y: y position
    :ivar level_position: position of level
    """

    __slots__ = 'x', 'y', 'level_position'

    def __init__(self, x: int, y: int, level_position: LevelPosition = None):
        self.x = x
        self.y = y
        self.level_position = level_position

    def __eq__(self, other: 'Position'):
        """True if coords and level_pos are same"""
        level_pos_eq = self.level_position == other.level_position if self.level_position else True  # fixme
        return self.x == other.x and self.y == other.y and level_pos_eq

    def __sub__(self, other: 'Position') -> Directions:
        """
        :return: direction between adjacent positions
        """
        if self.x > other.x:
            return Directions.left
        if self.x < other.x:
            return Directions.right
        if self.y > other.y:
            return Directions.top
        if self.y < other.y:
            return Directions.bottom

    def get_adjacent(self, direction: Directions):
        """:return: position of adjacent object by direction"""
        x, y = self.x, self.y
        match direction:
            case Directions.top:
                y -= 1
            case Directions.bottom:
                y += 1
            case Directions.left:
                x -= 1
            case Directions.right:
                x += 1
        return Position(x, y, self.level_position)

    def get(self):
        return self.x, self.y

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'level_position': self.level_position.to_dict()
        }
