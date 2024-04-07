from .cell import CELL, NoneCell
from ..global_env.enums import Directions
from ..global_env.types import LevelPosition, Position


class GameLevel:
    def __init__(self, level_position: LevelPosition, field: list[list[CELL]]):
        self.level_position: LevelPosition = level_position
        self.field: list[list[CELL]] = field

    def get_neighbour_cell(self, position: Position, direction: Directions) -> CELL | None:
        x, y = direction.get_neighbour_cords(position.x, position.y)
        try:
            return self.field[y][x]
        except IndexError:
            return None

    def set_cell(self, position: Position, new_cell: CELL):
        self.field[position.y][position.x] = new_cell

    def get_cell(self, position: Position) -> CELL:
        return self.field[position.y][position.x]

    def get_field_list(self) -> list[list[dict]]:
        return [[cell.to_dict() if type(cell) is not NoneCell else {} for cell in row] for row in self.field]

    def get_field_pattern_list(self) -> list[list[dict[str, int] | None]]:
        return [
            [{'x': cell.position.x, 'y': cell.position.y} if type(cell) is not NoneCell else None for cell in row[1:-1]]
            for row in self.field[1:-1]
        ]
