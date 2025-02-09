from typing import Union

from ...game_engine.field import wall
from ...game_engine.global_env.enums import Directions
from ...game_engine.global_env.types import Position


class UnknownWall(wall.WallEmpty):
    def __init__(self):
        super().__init__()


class UnbreakableWall(wall.WallOuter):
    def __init__(self):
        super().__init__()


class NoneCell:
    """

    Base bot Cell object

    :param position: position of cell
    :type position: Position
    :ivar walls: walls of cell
    :type walls: dict[Directions, WallEmpty]

    """

    def __init__(self, position: Position):
        self.position = position
        self.walls: dict[Directions, wall.WallEmpty] = {
            Directions.top: wall.WallEmpty(),
            Directions.right: wall.WallEmpty(),
            Directions.bottom: wall.WallEmpty(),
            Directions.left: wall.WallEmpty()}

    def add_wall(self, direction: Directions, new_wall: wall.WallEmpty):
        """add wall by direction"""
        self.walls[direction] = new_wall

    def __sub__(self, other: 'CELL') -> Directions | None:
        """
        :return: direction between adjacent cells
        """
        if not self.position.level_position == other.position.level_position:
            return None
        return self.position - other.position

    def __repr__(self):
        return '='


class Cell(NoneCell):
    """Ground Cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'c'


class CellRiver(Cell):
    """River cell object"""

    def __init__(self, position: Position, direction: Directions = None):
        super().__init__(position)
        self.river = []
        self.direction = direction

    def __repr__(self):
        match self.direction:
            case Directions.top:
                return '↑'
            case Directions.bottom:
                return '↓'
            case Directions.right:
                return '→'
            case Directions.left:
                return '←'
            case _:
                return 'r'


class CellRiverMouth(CellRiver):
    """River Mouth cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'y'


class CellExit(Cell):
    """Exit cell object"""

    def __init__(self, position: Position, direction: Directions):
        super().__init__(position)
        self.walls = {
            Directions.top: wall.WallOuter(),
            Directions.right: wall.WallOuter(),
            Directions.bottom: wall.WallOuter(),
            Directions.left: wall.WallOuter()}
        self.walls.update({direction: wall.WallEntrance()})

    def __repr__(self):
        return '🚪'


class CellClinic(Cell):
    """Clinic cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'H'


class CellArmory(Cell):
    """Armory cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'A'


class CellArmoryWeapon(CellArmory):
    """Armory Weapon cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'W'


class CellArmoryExplosive(CellArmory):
    """Armory Explosive cell object"""

    def __init__(self, position: Position):
        super().__init__(position)

    def __repr__(self):
        return 'E'


class UnknownCell(Cell):
    def __init__(self, position: Position):
        super().__init__(position)
        self.walls: dict[Directions, UnknownWall] = {
            Directions.top: UnknownWall(),
            Directions.right: UnknownWall(),
            Directions.bottom: UnknownWall(),
            Directions.left: UnknownWall()}

    def __repr__(self):
        return '?'


class PossibleExit(CellExit):
    def __init__(self, position: Position, direction: Directions):
        super().__init__(position, direction)

    def __repr__(self):
        return '?E'


CELL = Union[
    NoneCell, Cell,
    CellRiver, CellRiverMouth,
    CellExit, CellClinic, CellArmory,
    CellArmoryExplosive, CellArmoryWeapon,
    UnknownCell, PossibleExit
]
