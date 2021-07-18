from random import choice

from field.cell import *
from field.wall import *
from enums import Directions, RiverDirections
from entities.treasure import Treasure, TreasureTypes


class FieldGenerator:
    def __init__(self, cols, rows):
        self.pattern = []
        self.field = []
        self.rows = rows
        self.cols = cols
        self.generate_pattern()
        self.generate_field()
        self.generate_connections()
        outers = self.generate_outer_walls()
        self.create_exit(outers)
        self.treasures = self.spawn_treasures(2)

    def get_field(self):
        return self.field

    def get_treasures(self):
        return self.treasures

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
                    neighbours = {}
                    for direction in Directions:
                        x, y = direction.calc(col, row)
                        if x in range(0, self.cols) and y in range(0, self.rows) and self.pattern[y][x]:
                            neighbours.update({direction: self.field[y][x]})
                        else:
                            neighbours.update({direction: None})

                    self.field[row][col].change_neighbours(neighbours)

    def generate_outer_walls(self):
        outer_cells = set()
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if self.pattern[row][col]:
                    for direction in Directions:
                        if self.field[row][col].neighbours[direction] is None:
                            self.field[row][col].add_wall(direction, WallOuter())
                            outer_cells.add(self.field[row][col])

        return list(outer_cells)

    @staticmethod
    def create_exit(outer_cells):
        cell = choice(outer_cells)
        dirs = []
        for direction in Directions:
            if isinstance(cell.walls[direction], WallOuter):
                dirs.append(direction)
        direction = choice(dirs)
        cell.add_wall(direction, WallExit())
        cell.neighbours.update({direction: CellExit(*direction.calc(cell.x, cell.y), -direction, cell)})

    def spawn_treasures(self, amount):
        treasures = []
        ground_cells = []
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if self.pattern[row][col]:
                    if type(self.field[row][col]) == Cell:
                        ground_cells.append(self.field[row][col])

        cell = choice(ground_cells)
        ground_cells.remove(cell)
        treasures.append(Treasure(TreasureTypes.very, cell))

        for _ in range(amount-1):
            cell = choice(ground_cells)
            ground_cells.remove(cell)
            treasures.append(Treasure(TreasureTypes.spurious, cell))

        return treasures

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
    field[0].append(CellRiver(2, 0, RiverDirections.right))
    field[0].append(CellRiver(3, 0, RiverDirections.mouth))
    field[0].append(Cell(4, 0))
    field[1].append(CellRiver(0, 1, RiverDirections.right))
    field[1].append(CellRiver(1, 1, RiverDirections.right))
    field[1].append(CellRiver(2, 1, RiverDirections.top))
    field[1].append(Cell(3, 1))
    field[1].append(Cell(4, 1))
    field[2].append(Cell(0, 2))
    field[2].append(Cell(1, 2))
    field[2].append(CellArmory(2, 2))
    field[2].append(CellRiver(3, 2, RiverDirections.mouth))
    field[2].append(Cell(4, 2))
    field[3].append(CellClinic(0, 3))
    field[3].append(Cell(1, 3))
    field[3].append(CellRiver(2, 3, RiverDirections.right))
    field[3].append(CellRiver(3, 3, RiverDirections.top))
    field[3].append(Cell(4, 3))

    # field[0][1].add_wall(Directions.right, WallConcrete())
    # field[0][2].add_wall(Directions.left, WallConcrete())
    field[0][1].walls[Directions.right] = WallConcrete()
    field[0][2].walls[Directions.left] = WallConcrete()

    field[0][1].walls[Directions.bottom] = WallRubber()
    field[1][1].walls[Directions.top] = WallRubber()

    river_list = [field[1][0], field[1][1], field[1][2], field[0][2], field[0][3]]
    field[1][0].add_river_list(river_list)
    field[1][1].add_river_list(river_list)
    field[1][2].add_river_list(river_list)
    field[0][2].add_river_list(river_list)
    field[0][3].add_river_list(river_list)

    river_list = [field[3][2], field[3][3], field[2][3]]
    field[3][2].add_river_list(river_list)
    field[3][3].add_river_list(river_list)
    field[2][3].add_river_list(river_list)

    return field
