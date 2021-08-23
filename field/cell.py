from typing import Optional

from globalEnv.enums import Directions, TreasureTypes
from globalEnv.Exepts import WinningCondition
from field.wall import *
from entities.player import Player
from entities.treasure import Treasure


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
        :param direction:
        :return: True if wall was destroyed else False
        """
        if self.walls[direction].breakable:
            self.add_wall(direction, WallEmpty())
            neighbour = self.neighbours[direction]
            if neighbour and neighbour.walls[-direction].breakable:
                neighbour.walls[-direction] = WallEmpty()
            return True
        return False

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)

    def treasure_movement(self, treasure: Treasure):
        treasure.cell = self

    def check_wall(self, player: Player, direction: Directions) -> list[type]:
        pl_collision, pl_state, wall_type = self.walls[direction].handler()
        cell = self.neighbours[direction] if not pl_collision else self
        try:
            response = cell.active(player) if pl_state else cell.idle(player)
        except WinningCondition:
            raise
        else:
            return [wall_type] + response


class CellRiver(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.river = []

    def idle(self, player: Player) -> list[type]:
        idx = self.river.index(self)
        player.cell = self.river[idx + 1]
        return [type(player.cell)]

    def active(self, player: Player) -> list[type]:
        if self.__is_same_river(player):
            player.cell = self
            return [type(self)]
        else:
            idx = self.river.index(self)
            dif = len(self.river) - 1 - idx
            player.cell = self.river[idx + 2] if dif > 2 else self.river[idx + dif]
            return [type(self), type(player.cell)]

    def treasure_movement(self, treasure: Treasure):
        idx = self.river.index(self)

        if idx + 1 < len(self.river):
            treasure.cell = self.river[idx + 1]
        else:
            treasure.cell = self

    def __is_same_river(self, player: Player):
        if isinstance(player.cell, CellRiver) and player.cell is not self:
            if player.cell in self.river:
                if abs(self.river.index(self) - self.river.index(player.cell)) == 1:
                    return True

    def add_river_list(self, river):
        self.river = river


class CellRiverMouth(CellRiver):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)


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

    def active(self, player: Player) -> list[type]:  # todo есть мнение что афк обработчик должен возвращать на поле
        # todo есть мнение, что игрок без клада не может выйти
        player.cell = self
        if player.treasure:
            treasure = player.treasure
            player.treasure = None
            if treasure.t_type is TreasureTypes.very:
                raise WinningCondition()
        return [type(self)]


class CellClinic(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        player.health = player.health_max
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)


class CellArmory(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        player.bombs = player.bombs_max
        player.arrows = player.arrows_max
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)


class CellArmoryWeapon(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        player.arrows = player.arrows_max
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)


class CellArmoryExplosive(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player) -> list[type]:
        player.cell = self
        player.bombs = player.bombs_max
        return [type(self)]

    def active(self, player: Player) -> list[type]:
        return self.idle(player)
