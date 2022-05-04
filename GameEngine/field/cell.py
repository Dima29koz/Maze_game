from typing import Type

from GameEngine.globalEnv.enums import Directions
from GameEngine.field.wall import WallEmpty, WallOuter, WallEntrance


class Cell:
    """
    Base Cell object

    :param x: x coordinate of cell
    :type x: int
    :param y: y coordinate of cell
    :type y: int
    :ivar neighbours: neighbours of cell
    :type neighbours: dict[Directions, Cell | None]
    :ivar walls: walls of cell
    :type walls: dict[Directions, WallEmpty]

    """
    def __init__(self, x: int, y: int):
        self.x, self.y = x, y
        self.neighbours: dict[Directions, Cell | None] = {
            Directions.top: None,
            Directions.right: None,
            Directions.bottom: None,
            Directions.left: None}
        self.walls: dict[Directions, WallEmpty] = {
            Directions.top: WallEmpty(),
            Directions.right: WallEmpty(),
            Directions.bottom: WallEmpty(),
            Directions.left: WallEmpty()}

    def change_neighbours(self, neighbours: dict):
        """set cell neighbours"""
        self.neighbours = neighbours

    def add_wall(self, direction: Directions, wall: WallEmpty):
        """add wall by direction"""
        self.walls[direction] = wall

    def break_wall(self, direction: Directions) -> WallEmpty:
        """
        Break wall by direction if wall is breakable

        :return: wall that was broken
        """
        wall = self.walls[direction]
        if self.walls[direction].breakable:
            self.add_wall(direction, WallEmpty())
            neighbour = self.neighbours[direction]
            if neighbour and neighbour.walls[-direction].breakable:
                neighbour.walls[-direction] = WallEmpty()
        return wall

    def idle(self, previous_cell):
        """idle handler"""
        return self

    def active(self, previous_cell):
        """active handler"""
        return self.idle(previous_cell)

    def treasure_movement(self):
        """treasure movement handler"""
        return self

    def check_wall(self, direction: Directions) -> tuple[bool, bool, Type[WallEmpty]]:
        """return wall attributes"""
        return self.walls[direction].handler()

    def to_dict(self) -> dict:
        """converts cell to dict"""
        return {
            'type': self.__class__.__name__,
            'x': self.x,
            'y': self.y,
            'walls': {direction.name: wall.__class__.__name__ for direction, wall in self.walls.items()}
        }

    def __sub__(self, other) -> Directions:
        """
        :return: direction between adjacent cells
        """
        if self.x > other.x:
            return Directions.left
        if self.x < other.x:
            return Directions.right
        if self.y > other.y:
            return Directions.top
        if self.y < other.y:
            return Directions.bottom


class CellRiver(Cell):
    """River cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.river = []

    def idle(self, previous_cell):
        idx = self.river.index(self)
        return self.river[idx + 1]

    def active(self, previous_cell):
        if self.__is_same_river(previous_cell):
            return self
        else:
            idx = self.river.index(self)
            dif = len(self.river) - 1 - idx
            return self.river[idx + 2] if dif > 2 else self.river[idx + dif]

    def treasure_movement(self):
        index = self.river.index(self)
        return self.river[index + 1]

    def __is_same_river(self, previous_cell):
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


class CellRiverMouth(CellRiver):
    """River Mouth cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def treasure_movement(self):
        return self


class CellExit(Cell):
    """Exit cell object"""
    def __init__(self, x: int, y: int, direction: Directions, cell):
        super().__init__(x, y)
        self.neighbours[direction] = cell
        self.walls = {
            Directions.top: WallOuter(),
            Directions.right: WallOuter(),
            Directions.bottom: WallOuter(),
            Directions.left: WallOuter()}
        self.walls.update({direction: WallEntrance()})

    def active(self, previous_cell):  # todo есть мнение что афк обработчик должен возвращать на поле
        # todo есть мнение, что игрок без клада не может выйти
        return self


class CellClinic(Cell):
    """Clinic cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmory(Cell):
    """Armory cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmoryWeapon(CellArmory):
    """Armory Weapon cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmoryExplosive(CellArmory):
    """Armory Explosive cell object"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)
