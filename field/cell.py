from typing import Optional

from globalEnv.enums import Directions
from field.wall import *


class Cell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.neighbours: dict[Directions, Optional[Cell]] = {
            Directions.top: None,
            Directions.right: None,
            Directions.bottom: None,
            Directions.left: None}
        self.walls = {
            Directions.top: WallEmpty(),
            Directions.right: WallEmpty(),
            Directions.bottom: WallEmpty(),
            Directions.left: WallEmpty()}

    def change_neighbours(self, neighbours):
        self.neighbours = neighbours

    def add_wall(self, direction, wall):
        self.walls[direction] = wall

    def break_wall(self, direction: Directions):
        """
        Уничтожает стену в заданном направлении если стена разрушима

        :return: hit wall
        """
        wall = self.walls[direction]
        if self.walls[direction].breakable:
            self.add_wall(direction, WallEmpty())
            neighbour = self.neighbours[direction]
            if neighbour and neighbour.walls[-direction].breakable:
                neighbour.walls[-direction] = WallEmpty()
        return wall

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)

    def treasure_movement(self):
        return self

    def check_wall(self, direction: Directions):
        return self.walls[direction].handler()


class CellRiver(Cell):
    def __init__(self, x, y):
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
        idx = self.river.index(self)
        return self.river[idx + 1]

    def __is_same_river(self, previous_cell):
        if isinstance(previous_cell, CellRiver) and previous_cell is not self:
            if previous_cell in self.river:
                if abs(self.river.index(self) - self.river.index(previous_cell)) == 1:
                    return True

    def add_river_list(self, river):
        self.river = river


class CellRiverMouth(CellRiver):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellExit(Cell):
    def __init__(self, x, y, direction, cell):
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
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmory(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmoryWeapon(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)


class CellArmoryExplosive(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, previous_cell):
        return self

    def active(self, previous_cell):
        return self.idle(previous_cell)
