from field.cell import *
from field.wall import *
from enums import Directions


class FieldGenerator:
    def __init__(self, cols, rows):
        self.pattern = []
        self.field = []
        self.rows = rows
        self.cols = cols
        self.generate_pattern()
        self.generate_field()
        self.generate_connections()

    def get_field(self):
        return self.field

    def generate_pattern(self):
        self.pattern = [[True] * self.cols for _ in range(self.rows)]

    def generate_field(self):
        self.field = create_test_field()
        # self.field = [[0] * self.cols for i in range(self.rows)]
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

    def create_base_field(self):
        pass

        # def gen_river_source(self):
        #     a = random.randint(0, len(self.grid) - 1)
        #     b = random.randint(0, len(self.grid[0]) - 1)
        #     return a, b
        #
        # def gen_river(self, length):
        #     river = []
        #     tmpgrid = [[True] * len(self.grid[0]) for i in range(len(self.grid))]
        #     while any(any(x) for x in tmpgrid):
        #         x, y = self.gen_river_source()
        #         tmpgrid[x][y] = False
        #         if isinstance(self.grid[x][y], Cell):
        #             self.grid[x][y] = CellRiver(self.grid[x][y].right_cell, self.grid[x][y].left_cell,
        #                                         self.grid[x][y].top_cell, self.grid[x][y].bottom_cell, river)
        #             river.append(self.grid[x][y])
        #             river = self.gen_next_river_cell(length - 1, river)
        #         if len(river):
        #             pass
        #
        # def gen_next_river_cell(self, length, river):
        #     pass


def create_test_field():
    row = 4
    field = [[] for _ in range(row)]
    field[0].append(Cell(0, 0))
    field[0].append(Cell(1, 0))
    field[0].append(CellRiver(2, 0, Directions.right))
    field[0].append(CellRiver(3, 0, Directions.mouth))
    field[0].append(Cell(4, 0))
    field[1].append(CellRiver(0, 1, Directions.right))
    field[1].append(CellRiver(1, 1, Directions.right))
    field[1].append(CellRiver(2, 1, Directions.top))
    field[1].append(Cell(3, 1))
    field[1].append(Cell(4, 1))
    field[2].append(Cell(0, 2))
    field[2].append(Cell(1, 2))
    field[2].append(Cell(2, 2))
    field[2].append(CellRiver(3, 2, Directions.mouth))
    field[2].append(Cell(4, 2))
    field[3].append(Cell(0, 3))
    field[3].append(Cell(1, 3))
    field[3].append(CellRiver(2, 3, Directions.right))
    field[3].append(CellRiver(3, 3, Directions.top))
    field[3].append(Cell(4, 3))

    field[0][1].walls[Directions.right] = WallConcrete()
    field[0][2].walls[Directions.left] = WallConcrete()

    field[0][0].walls[Directions.top] = WallOuter()
    field[0][0].walls[Directions.left] = WallOuter()

    field[1][0].river = [field[1][0], field[1][1], field[1][2], field[0][2], field[0][3]]
    field[1][1].river = field[1][2].river = field[0][2].river = field[0][3].river = field[1][0].river

    field[3][2].river = [field[3][2], field[3][3], field[2][3]]
    field[3][3].river = field[3][2].river
    field[2][3].river = field[3][2].river
    return field


def create_test_field2():
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

    field[0][1].walls[Directions.right] = WallConcrete()
    field[0][2].walls[Directions.left] = WallConcrete()

    field[0][0].walls[Directions.top] = WallOuter()
    field[0][0].walls[Directions.left] = WallOuter()

    return field
