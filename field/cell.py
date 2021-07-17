from enums import Directions
from field.wall import *
from entities.player import Player
from field.wall import WallEmpty


class Cell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.neighbours = {
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

    def idle(self, player: Player):
        """idle обработчик пустой клетки"""
        print(f"idle ({self.x}, {self.y})")
        player.cell = self

    def active(self, player):
        """active обработчик пустой клетки"""
        print(f"active ({self.x}, {self.y})")
        player.cell = self

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
    def __init__(self, x, y, direction=Directions.mouth):
        super().__init__(x, y)
        self.direction = direction
        self.river = []

    def idle(self, player):
        try:
            player.cell = self.neighbours[self.direction]
        except KeyError:
            player.cell = self

    def active(self, player: Player):
        if isinstance(player.cell, CellRiver) and player.cell in self.river:
            player.cell = self
        else:
            idx = self.river.index(self)
            if idx + 2 < len(self.river):
                player.cell = self.river[idx + 2]
            elif idx + 1 < len(self.river):
                player.cell = self.river[idx + 1]
            else:
                player.cell = self


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
