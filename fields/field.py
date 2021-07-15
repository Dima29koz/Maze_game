from cell import *
from logic import dir_calc, is_same_river
from field_generator import FieldGenerator
from player import Player

class Field:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid_cells = FieldGenerator(rows, cols).get_field()

    def get_grid(self):
        return self.grid_cells

    def to_lineal(self, x, y):
        return x + y * self.cols

    def move_calc(self, player: Player):
        x, y = player.cell.x, player.cell.y
        direction = player.direction
        cell = self.grid_cells[self.to_lineal(x, y)]
        if direction == Directions.mouth:
            """пропуск хода"""
            cell.idle(player)
        else:
            new_x, new_y, state = cell.walls[direction].handler(x, y, direction)
            idx = self.to_lineal(new_x, new_y)
            new_cell = self.grid_cells[idx]

            new_cell.active(player, cell)
            # self.grid_cells[self.to_lineal(player.cell.x, player.cell.y)].idle(player)
        print(player.cell.x, player.cell.y)

    # def river_calc(self, x, y):
    #     idx = self.to_lineal(x, y)
    #     cell = self.grid_cells[idx]
    #     for _ in range(2):
    #         if cell.direction is Directions.mouth:
    #             break
    #         x, y = dir_calc(x, y, cell.direction)
    #         idx = self.to_lineal(x, y)
    #         cell = self.grid_cells[idx]
    #     return x, y
