from game_core.game_engine.field.cell import CELL, NoneCell
from game_core.game_engine.global_env.enums import Directions
from game_core.game_engine.global_env.types import LevelPosition, Position


class GameLevel:
    def __init__(self, level_position: LevelPosition, field: list[list[CELL]]):
        self.level_position: LevelPosition = level_position
        self.field: list[list[CELL]] = field

    def get_neighbour_cell(self, position: Position, direction: Directions):
        x, y = position.get_adjacent(direction).get()
        try:
            return self.field[y][x]
        except IndexError:
            return None

    def set_cell(self, position: Position, new_cell: CELL):
        self.field[position.y][position.x] = new_cell

    def get_cell(self, position: Position):
        return self.field[position.y][position.x]

    def get_field_list(self):
        return [[cell.to_dict() if type(cell) is not NoneCell else {} for cell in row] for row in self.field]

    def get_field_pattern_list(self):
        return [
            [{'x': cell.position.x, 'y': cell.position.y} if type(cell) is not NoneCell else None for cell in row[1:-1]]
            for row in self.field[1:-1]
        ]
