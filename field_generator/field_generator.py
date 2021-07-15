from field_v2.cell import *
from fields.logic import Directions


class FieldGenerator:
    def __init__(self, cols, rows):
        self.pattern = []
        self.field = [[0] * cols for i in range(rows)]
        self.rows = rows
        self.cols = cols
        self.generate_pattern()
        self.generate_field()
        self.generate_connections()

    def generate_pattern(self):
        self.pattern = [[True] * self.cols for _ in range(self.rows)]

    def generate_field(self):
        self.field = create_test_field3()
        # for row in range(self.rows):
        #     for col in range(self.cols):
        #         if self.pattern[row][col]:
        #             self.field[row][col] = Cell(col, row)

    def generate_connections(self):
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if self.pattern[row][col]:
                    neighbours = {
                       Directions.left: self.field[row][col - 1] if col - 1 in range(0, self.cols) and self.pattern[row][col - 1] else None,
                       Directions.bottom: self.field[row + 1][col] if row + 1 in range(0, self.rows) and self.pattern[row+1][col] else None,
                       Directions.right: self.field[row][col + 1] if col + 1 in range(0, self.cols) and self.pattern[row][col + 1] else None,
                       Directions.top: self.field[row - 1][col] if row - 1 in range(0, self.rows) and self.pattern[row-1][col] else None}
                    self.field[row][col].change_neighbours(neighbours)

    def print(self):
        for i in range(self.rows):
            print(*self.field[i])

    def get_field(self):
        return self.field

    def create_base_field(self):
        pass

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
def create_test_field3():
    cols = 5
    row = 4
    field = [[] for _ in range(row)]
    field[0].append(Cell(0, 0))
    field[0].append(Cell(1, 0))
    field[0].append(CellRiver(2, 0, Directions.right))
    field[0].append(CellRiver(3, 0, Directions.mouth))
    field[0].append(CellRiver(4, 0, Directions.mouth))
    field[1].append(CellRiver(0, 1, Directions.right))
    field[1].append(CellRiver(1, 1, Directions.right))
    field[1].append(CellRiver(2, 1, Directions.top))
    field[1].append(CellRiver(3, 1, Directions.right))
    field[1].append(CellRiver(4, 1, Directions.top))
    field[2].append(CellRiver(0, 2, Directions.right))
    field[2].append(CellRiver(1, 2, Directions.right))
    field[2].append(CellRiver(2, 2, Directions.right))
    field[2].append(CellRiver(3, 2, Directions.right))
    field[2].append(CellRiver(4, 2, Directions.bottom))
    field[3].append(CellRiver(0, 3, Directions.mouth))
    field[3].append(CellRiver(1, 3, Directions.left))
    field[3].append(CellRiver(2, 3, Directions.left))
    field[3].append(CellRiver(3, 3, Directions.left))
    field[3].append(CellRiver(4, 3, Directions.left))

    # field[1].walls[Directions.right] = WallConcrete()
    # field[2].walls[Directions.left] = WallConcrete()

    # field[0].walls[Directions.top] = WallOuter()
    # field[0].walls[Directions.left] = WallOuter()

    return field
