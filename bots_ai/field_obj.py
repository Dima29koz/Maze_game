from GameEngine.field import wall, cell
from GameEngine.globalEnv.enums import Directions


class UnknownWall(wall.WallEmpty):
    def __init__(self):
        super().__init__()


class UnbreakableWall(wall.WallOuter):
    def __init__(self):
        super().__init__()


class UnknownCell(cell.Cell):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.x, self.y = x, y
        self.neighbours: dict[Directions, cell.Cell | None] = {
            Directions.top: None,
            Directions.right: None,
            Directions.bottom: None,
            Directions.left: None}
        self.walls: dict[Directions, UnknownWall] = {
            Directions.top: UnknownWall(),
            Directions.right: UnknownWall(),
            Directions.bottom: UnknownWall(),
            Directions.left: UnknownWall()}

    def __repr__(self):
        return '?'
