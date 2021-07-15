from fields.logic import Directions
from field_v2.wall import WallEmpty, WallConcrete


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

    def __str__(self):
        return "Суша"


class CellRiver(Cell):
    def __init__(self, x, y, direction=Directions.mouth):
        super().__init__(x, y)
        self.direction = direction
        self.river = []

    def __str__(self):
        return "река"
