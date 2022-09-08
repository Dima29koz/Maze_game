from GameEngine.globalEnv.enums import Directions


class Position:
    """
    describes the position of an object
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: 'Position'):
        return self.x == other.x and self.y == other.y

    def __sub__(self, other) -> Directions:
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
        return Position(x, y)

    def get(self):
        return self.x, self.y
