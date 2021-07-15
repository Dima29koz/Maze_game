from field_v2.cell import *
from fields.logic import Directions


class FieldGenerator:
    def __init__(self, cols, rows):
        self.rows = rows
        self.cols = cols
        self.field = [[None] * self.rows for i in range(self.cols)]

    def print(self):
        for i in range(self.cols):
            print(*self.field[i])

    def get_field(self):
        return self.field

    def create_base_field(self):
        return [Cell(col, row) for row in range(self.rows) for col in range(self.cols)]

    def create_test_field(self):
        field = []
        field.append(Cell(0, 0))
        field.append(Cell(1, 0))
        field.append(CellRiver(2, 0, Directions.right))
        field.append(CellRiver(3, 0, Directions.mouth))
        field.append(Cell(4, 0))
        field.append(CellRiver(0, 1, Directions.right))
        field.append(CellRiver(1, 1, Directions.right))
        field.append(CellRiver(2, 1, Directions.top))
        field.append(Cell(3, 1))
        field.append(Cell(4, 1))
        field.append(Cell(0, 2))
        field.append(Cell(1, 2))
        field.append(Cell(2, 2))
        field.append(CellRiver(3, 2, Directions.mouth))
        field.append(Cell(4, 2))
        field.append(Cell(0, 3))
        field.append(Cell(1, 3))
        field.append(CellRiver(2, 3, Directions.right))
        field.append(CellRiver(3, 3, Directions.top))
        field.append(Cell(4, 3))
        self.field = field


# def create_test_field2():
#     field = []
#     field.append(CellGround(0, 0))
#     field.append(CellGround(1, 0))
#     field.append(CellRiver(2, 0, Directions.right))
#     field.append(CellRiver(3, 0, Directions.mouth))
#     field.append(CellRiver(4, 0, Directions.mouth))
#     field.append(CellRiver(0, 1, Directions.right))
#     field.append(CellRiver(1, 1, Directions.right))
#     field.append(CellRiver(2, 1, Directions.top))
#     field.append(CellRiver(3, 1, Directions.right))
#     field.append(CellRiver(4, 1, Directions.top))
#     field.append(CellGround(0, 2))
#     field.append(CellGround(1, 2))
#     field.append(CellGround(2, 2))
#     field.append(CellRiver(3, 2, Directions.mouth))
#     field.append(CellGround(4, 2))
#     field.append(CellGround(0, 3))
#     field.append(CellGround(1, 3))
#     field.append(CellRiver(2, 3, Directions.right))
#     field.append(CellRiver(3, 3, Directions.top))
#     field.append(CellGround(4, 3))
#     return field
#
#
# def create_test_field3():
#     field = []
#     field.append(CellGround(0, 0))
#     field.append(CellGround(1, 0))
#     field.append(CellRiver(2, 0, Directions.right))
#     field.append(CellRiver(3, 0, Directions.mouth))
#     field.append(CellRiver(4, 0, Directions.mouth))
#     field.append(CellRiver(0, 1, Directions.right))
#     field.append(CellRiver(1, 1, Directions.right))
#     field.append(CellRiver(2, 1, Directions.top))
#     field.append(CellRiver(3, 1, Directions.right))
#     field.append(CellRiver(4, 1, Directions.top))
#     field.append(CellRiver(0, 2, Directions.right))
#     field.append(CellRiver(1, 2, Directions.right))
#     field.append(CellRiver(2, 2, Directions.right))
#     field.append(CellRiver(3, 2, Directions.right))
#     field.append(CellRiver(4, 2, Directions.bottom))
#     field.append(CellRiver(0, 3, Directions.mouth))
#     field.append(CellRiver(1, 3, Directions.left))
#     field.append(CellRiver(2, 3, Directions.left))
#     field.append(CellRiver(3, 3, Directions.left))
#     field.append(CellRiver(4, 3, Directions.left))
#
#     field[1].walls[Directions.right] = WallConcrete()
#     field[2].walls[Directions.left] = WallConcrete()
#
#     field[0].walls[Directions.top] = WallOuter()
#     field[0].walls[Directions.left] = WallOuter()
#
#     return field
