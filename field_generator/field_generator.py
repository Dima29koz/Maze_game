from random import choice, shuffle
import random
from copy import deepcopy
from field.cell import *
from field.wall import *
from enums import Directions, RiverDirections
from entities.treasure import Treasure, TreasureTypes
from level_pattern import PatternCell

class FieldGenerator:
    def __init__(self, cols, rows):
        self.pattern: list[list[PatternCell]] = [[]]
        self.field: list[list[Cell]] = [[]]
        self.rows = rows
        self.cols = cols
        self.generate_pattern()
        self.generate_field()
        # self.generate_connections()
        # outers = self.generate_outer_walls()
        # self.create_exit(outers)
        # self.treasures = self.spawn_treasures(2)

    def get_field(self):
        return self.field

    def get_treasures(self):
        return self.treasures

    def generate_pattern(self):
        # self.pattern = [[True] * self.cols for _ in range(self.rows)]
        self.pattern = [[PatternCell(col, row) for col in range(self.cols)] for row in range(self.rows)]
        for i in range(5):
            self.pattern[0][i].is_not_none = False
            self.pattern[1][i].is_not_none = False
        self.pattern[3][0].is_not_none = False
        self.pattern[3][3].is_not_none = False
        self.pattern[3][4].is_not_none = False

    def generate_field(self):
        # self.field = create_test_field()
        self.field = [[Cell(col, row) if self.pattern[row][col].is_not_none else None
                       for col in range(self.cols)] for row in range(self.rows)]

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

    @staticmethod
    def gen_river_source(allowed_sources):
        if allowed_sources:
            source = choice(allowed_sources)
            allowed_sources.remove(source)
            return source
        else:
            return False

    def gen_river(self, length):
        field = deepcopy(self.field)
        pattern = deepcopy(self.pattern)
        allowed_sources = []
        for row in range(self.rows):
            for col in range(self.cols):
                if type(self.field[row][col]) == Cell:
                    allowed_sources.append(self.field[row][col])

        start = self.gen_river_source(allowed_sources)
        river = []
        while start:
            river = [start]
            river = self.gen_next_river_cell(length-1, pattern, river)
            if not river:
                start = self.gen_river_source(allowed_sources)
            else:
                break

        draw_field(field, self.rows, self.cols, river)

    def check_directions(self, pattern: list[list[PatternCell]], current_cell):
        empty_neighbours = []
        for direction in Directions:
            x, y = direction.calc(current_cell.x, current_cell.y)
            if x in range(0, self.cols) and y in range(0, self.rows) and not pattern[y][x].visited and pattern[y][x].is_not_none:
                empty_neighbours.append(pattern[y][x])
        return empty_neighbours

    def gen_next_river_cell(self, length, pattern, river):
        if length == 0:
            return river
        else:
            empty_neighbours = self.check_directions(pattern, river[-1])

            while empty_neighbours:
                next_cell = choice(empty_neighbours)
                empty_neighbours.remove(next_cell)
                pattern[river[-1].y][river[-1].x].visited = True
                river.append(next_cell)
                a = self.gen_next_river_cell(length - 1, pattern, river)
                if a:
                    return a
            else:
                last = river.pop()

                pattern[last.y][last.x].visited = False

                return False

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


def draw_field(field, rows, cols, river):
    res = [['  ' for __ in range(cols)] for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            if field[row][col] is not None:
                res[row][col] = 'G '
    if river:
        for i, riv in enumerate(river):
            res[riv.y][riv.x] = f'R{i}'

    for row in range(rows):
        print(*res[row])



if __name__ == "__main__":
    f = FieldGenerator(5, 4)
    # draw_field(f.field, f.rows, f.cols)

    f.gen_river(6)
