from walls import *
from logic import dir_calc, Directions
from player import Player

class Cell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.walls = {
            Directions.top: WallEmpty(),
            Directions.right: WallEmpty(),
            Directions.bottom: WallEmpty(),
            Directions.left: WallEmpty()}

    def idle(self, player: Player):
        """idle обработчик пустой клетки не взаимодействует с игроком"""
        player.move(self)

    def active(self, player: Player, cell=None):
        """active обработчик пустой клетки не взаимодействует с игроком"""
        self.idle(player)

    def get_cell(self, f):
        pass

    def remove_walls(self, other):
        dx = self.x - other.x
        if dx == 1:
            self.walls[Directions.left] = WallEmpty()
            other.walls[Directions.right] = WallEmpty()
        elif dx == -1:
            self.walls[Directions.right] = WallEmpty()
            other.walls[Directions.left] = WallEmpty()
        dy = self.y - other.y
        if dy == 1:
            self.walls[Directions.top] = WallEmpty()
            other.walls[Directions.bottom] = WallEmpty()
        elif dy == -1:
            self.walls[Directions.bottom] = WallEmpty()
            other.walls[Directions.top] = WallEmpty()


class CellGround(Cell):
    def __init__(self, x, y):
        super().__init__(x, y)

    def get_color(self):
        return 107, 98, 60

    def get_info(self):
        return "surface"


class CellRiver(Cell):
    def __init__(self, x, y, direction):
        super().__init__(x, y)
        self.direction = direction

    def idle(self, player: Player):
        print("плыву")
        player.move(self)
        # player.move(*dir_calc(self.x, self.y, self.direction))

    def active(self, player: Player, cell=None):
        print("Смыло")

        if self.__is_same_river(cell, player):
            # перемещение против или по течению
            print("same river")
            player.move(self)
        else:
            # река должна смыть на 2 клетки по течению
            # player.move(*self.river_calc())
            # player.move(*dir_calc(self.x, self.y, self.direction))
            pass

    def __is_same_river(self, old_cell, player):
        if isinstance(old_cell, CellRiver):
            if old_cell.direction == player.direction:
                return True
            if self.direction == Directions.top and player.direction == Directions.bottom:
                return True
            if self.direction == Directions.bottom and player.direction == Directions.top:
                return True
            if self.direction == Directions.left and player.direction == Directions.right:
                return True
            if self.direction == Directions.right and player.direction == Directions.left:
                return True
        return False

    # def river_calc(self):
    #     idx = self.to_lineal(x, y)
    #     cell = self.grid_cells[idx]
    #     for _ in range(2):
    #         if cell.direction is Directions.mouth:
    #             break
    #         x, y = dir_calc(x, y, cell.direction)
    #         idx = self.to_lineal(x, y)
    #         cell = self.grid_cells[idx]
    #     return x, y

    def get_color(self):
        return 62, 105, 171

    def get_info(self):
        if self.direction == Directions.mouth:
            return "mouth"
        return "river"
