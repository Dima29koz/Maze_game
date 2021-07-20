from typing import Optional

from enums import Directions, TreasureTypes
from field.wall import *
from entities.player import Player
from entities.treasure import Treasure
from field.wall import WallEmpty


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

    def idle(self, player: Player):
        """idle обработчик пустой клетки"""
        print(f"idle ({self.x}, {self.y})")
        player.cell = self

    def active(self, player: Player):
        """active обработчик пустой клетки"""
        print(f"active ({self.x}, {self.y})")
        player.cell = self

    def treasure_movement(self, treasure: Treasure):
        treasure.cell = self

    def check_wall(self, player):
        state, moved = self.walls[player.direction].handler()
        if moved:
            cell = self.neighbours[player.direction]
        else:
            cell = self
        if state:
            return cell.active(player)
        else:
            return cell.idle(player)


class CellRiver(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.river = []

    def idle(self, player: Player):

        idx = self.river.index(self)

        if idx + 1 < len(self.river):
            player.cell = self.river[idx + 1]
        else:
            player.cell = self

    def active(self, player: Player):
        if self.__is_same_river(player):
            player.cell = self
        else:
            idx = self.river.index(self)
            dif = len(self.river) - 1 - idx
            player.cell = self.river[idx + 2] if dif > 2 else self.river[idx + dif]

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

    def active(self, player: Player):
        super().active(player)
        if player.treasure:
            treasure = player.treasure
            player.treasure = None
            if treasure.t_type is TreasureTypes.very:
                print("player wins")
            else:
                print(treasure.t_type)


class CellClinic(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player):
        player.cell = self
        player.health = player.health_max
        print("healed")

    def active(self, player: Player):
        self.idle(player)


class CellArmory(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player):
        player.cell = self
        player.bombs = player.bombs_max
        player.arrows = player.arrows_max
        print("ammunition restored")

    def active(self, player: Player):
        self.idle(player)


class CellArmoryWeapon(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player):
        player.cell = self
        player.arrows = player.arrows_max
        print("weapon restored")

    def active(self, player: Player):
        self.idle(player)


class CellArmoryExplosive(CellArmory):
    def __init__(self, x, y):
        super().__init__(x, y)

    def idle(self, player: Player):
        player.cell = self
        player.bombs = player.bombs_max
        print("Explosive restored")

    def active(self, player: Player):
        self.idle(player)
