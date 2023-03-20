from game_core.game_engine.field import wall, cell
from game_core.game_engine.global_env.enums import Directions
from game_core.game_engine.global_env.types import Position


class UnknownWall(wall.WallEmpty):
    def __init__(self):
        super().__init__()


class UnbreakableWall(wall.WallOuter):
    def __init__(self):
        super().__init__()


class UnknownCell(cell.Cell):
    def __init__(self, position: Position):
        super().__init__(position)
        self.walls: dict[Directions, UnknownWall] = {
            Directions.top: UnknownWall(),
            Directions.right: UnknownWall(),
            Directions.bottom: UnknownWall(),
            Directions.left: UnknownWall()}

    def __repr__(self):
        return '?'


class PossibleExit(cell.CellExit):
    def __init__(self, position: Position, direction: Directions):
        super().__init__(position, direction)

    def __repr__(self):
        return '?E'
