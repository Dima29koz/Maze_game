from .cell import CellExit, CELL
from .game_level import GameLevel
from ..global_env.types import Position, LevelPosition


class GameMap:
    def __init__(self):
        self.game_map: list[GameLevel] = []
        self.exit_cells: list[CellExit] = []

    def get_level(self, level_position: LevelPosition) -> GameLevel | None:
        for level in self.game_map:
            if level.level_position == level_position:
                return level
        return

    def get_cell(self, position: Position) -> CELL:
        return self.get_level(position.level_position).get_cell(position)
