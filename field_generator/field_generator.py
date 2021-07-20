from random import choice

from field.cell import *
from field.wall import *
from enums import Directions
from entities.treasure import Treasure, TreasureTypes
from field_generator.level_pattern import PatternCell
from field_generator.river_generator import RiverGenerator


class FieldGenerator:
    def __init__(self, cols, rows):
        self.rows = rows
        self.cols = cols
        self.pattern: list[list[PatternCell]] = [[]]
        self.ground_cells: list[Cell] = []
        self.field: list[list[Cell]] = [[]]
        self.treasures: list[Treasure] = []
        self.generate_field(rules=None)

    def get_field(self):
        return self.field

    def get_treasures(self):
        return self.treasures

    def generate_field(self, rules):
        self.generate_pattern()
        self.generate_base_field()
        self.generate_rivers(river_rules=[5, 3])
        self.generate_armory()
        self.generate_clinic()
        self.generate_connections()
        outer_cells = self.generate_outer_walls()
        self.create_exit(outer_cells)
        self.treasures = self.spawn_treasures(treasures_rules=[1, 1, 0])

    def generate_pattern(self):
        self.pattern = [[PatternCell(col, row) for col in range(self.cols)] for row in range(self.rows)]
        # for i in range(5):
        #     self.pattern[0][i].is_not_none = False
        #     self.pattern[1][i].is_not_none = False
        self.pattern[3][0].is_not_none = False
        self.pattern[3][3].is_not_none = False
        self.pattern[3][4].is_not_none = False

        self.pattern[1][2].is_not_none = False

    def generate_base_field(self):
        self.field = [[Cell(col, row) if self.pattern[row][col].is_not_none else None
                       for col in range(self.cols)] for row in range(self.rows)]

        ground_cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                if type(self.field[row][col]) == Cell:
                    ground_cells.append(self.field[row][col])
        self.ground_cells = ground_cells

    def generate_rivers(self, river_rules: list[int]):
        rg = RiverGenerator(self.cols, self.rows, self.pattern, self.field, self.ground_cells)
        rg.spawn_rivers(river_rules)

    def generate_armory(self):
        cell = choice(self.ground_cells)
        self.field[cell.y][cell.x] = CellArmory(cell.x, cell.y)
        self.ground_cells.remove(cell)

    def generate_clinic(self):
        cell = choice(self.ground_cells)
        self.field[cell.y][cell.x] = CellClinic(cell.x, cell.y)
        self.ground_cells.remove(cell)

    def generate_connections(self):
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if isinstance(self.field[row][col], Cell):
                    neighbours = {}
                    for direction in Directions:
                        x, y = direction.calc(col, row)
                        if x in range(self.cols) and y in range(self.rows) and isinstance(self.field[y][x], Cell):
                            neighbours.update({direction: self.field[y][x]})
                        else:
                            neighbours.update({direction: None})

                    self.field[row][col].change_neighbours(neighbours)

    def generate_outer_walls(self):
        outer_cells = set()
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if isinstance(self.field[row][col], Cell):
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

    def spawn_treasures(self, treasures_rules: list[int]):
        treasures = []

        treasure_cells = set()
        while len(treasure_cells) < sum(treasures_rules):
            treasure_cells.add(choice(self.ground_cells))

        for _ in range(treasures_rules[0]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.very, cell))

        for _ in range(treasures_rules[1]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.spurious, cell))

        for _ in range(treasures_rules[2]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.mined, cell))

        return treasures
