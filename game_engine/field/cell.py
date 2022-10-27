from typing import Type, Union

from game_engine.global_env.enums import Directions
from game_engine.global_env.types import Position, LevelPosition
from game_engine.field.wall import WallEmpty, WallOuter, WallEntrance


class NoneCell:
    """

    Base Cell object

    :param position: position of cell
    :type position: Position
    :ivar walls: walls of cell
    :type walls: dict[Directions, WallEmpty]

    """
    def __init__(self, position: Position):
        self.position = position
        self.walls: dict[Directions, WallEmpty] = {
            Directions.top: WallEmpty(),
            Directions.right: WallEmpty(),
            Directions.bottom: WallEmpty(),
            Directions.left: WallEmpty()}

    def add_wall(self, direction: Directions, wall: WallEmpty):
        """add wall by direction"""
        self.walls[direction] = wall

    def check_wall(self, direction: Directions) -> tuple[bool, bool, Type[WallEmpty]]:
        """return wall attributes"""
        return self.walls[direction].handler()

    def idle(self, previous_cell) -> 'CELL':
        """idle handler"""
        raise NotImplementedError

    def active(self, previous_cell) -> 'CELL':
        """active handler"""
        raise NotImplementedError

    def treasure_movement(self) -> 'CELL':
        """treasure movement handler"""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """converts cell to dict"""
        return self.position.to_dict() | {
            'type': self.__class__.__name__,
            'walls': {direction.name: wall.__class__.__name__ for direction, wall in self.walls.items()}
        }

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

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def treasure_movement(self):
        return self

    def __repr__(self):
        return 'c'


class CellRiver(Cell):
    """River cell object"""
    def __init__(self, position: Position, direction: Directions = None):
        super().__init__(position)
        self.river = []
        self.direction = direction

    def idle(self, previous_cell):
        idx = self.river.index(self)
        return self.river[idx + 1]

    def active(self, previous_cell):
        if self._is_same_river(previous_cell):
            return self
        else:
            idx = self.river.index(self)
            dif = len(self.river) - 1 - idx
            return self.river[idx + 2] if dif > 2 else self.river[idx + dif]

    def treasure_movement(self):
        index = self.river.index(self)
        return self.river[index + 1]

    def _is_same_river(self, previous_cell):
        if isinstance(previous_cell, CellRiver) and previous_cell is not self:
            if previous_cell in self.river:
                if abs(self.river.index(self) - self.river.index(previous_cell)) == 1:
                    return True

    def add_river_list(self, river):
        self.river = river

    def to_dict(self):
        sup = super().to_dict()
        idx = self.river.index(self)
        try:
            next_river_cell = self.river[idx + 1]
        except IndexError:
            direction = 'mouth'
        else:
            direction = (self - next_river_cell).name

        riv_dict = {'river_dir': direction}
        sup |= riv_dict
        return sup

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


class CellRiverBridge(CellRiver):
    def __init__(self, position: Position, direction: Directions = None):
        super().__init__(position, direction)

    def active(self, previous_cell):
        return self


class CellRiverMouth(CellRiver):
    """River Mouth cell object"""
    def __init__(self, position: Position):
        super().__init__(position)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def treasure_movement(self):
        return self

    def __repr__(self):
        return 'y'


class CellExit(Cell):
    """Exit cell object"""
    def __init__(self, position: Position, direction: Directions):
        super().__init__(position)
        self.walls = {
            Directions.top: WallOuter(),
            Directions.right: WallOuter(),
            Directions.bottom: WallOuter(),
            Directions.left: WallOuter()}
        self.walls.update({direction: WallEntrance()})

    def active(self, previous_cell):  # todo есть мнение что афк обработчик должен возвращать на поле
        # todo есть мнение, что игрок без клада не может выйти
        return self

    def __repr__(self):
        return 'exit'


class CellClinic(Cell):
    """Clinic cell object"""
    def __init__(self, position: Position):
        super().__init__(position)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def __repr__(self):
        return 'H'


class CellArmory(Cell):
    """Armory cell object"""
    def __init__(self, position: Position):
        super().__init__(position)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def __repr__(self):
        return 'A'


class CellArmoryWeapon(CellArmory):
    """Armory Weapon cell object"""
    def __init__(self, position: Position):
        super().__init__(position)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def __repr__(self):
        return 'W'


class CellArmoryExplosive(CellArmory):
    """Armory Explosive cell object"""
    def __init__(self, position: Position):
        super().__init__(position)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def __repr__(self):
        return 'E'


CELL = Union[
    NoneCell, Cell,
    CellRiver, CellRiverMouth, CellRiverBridge,
    CellExit, CellClinic, CellArmory,
    CellArmoryExplosive, CellArmoryWeapon,
]
