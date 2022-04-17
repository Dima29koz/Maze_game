from random import choice, sample, randint

from GameEngine.globalEnv.enums import Directions
from GameEngine.entities.treasure import Treasure, TreasureTypes
from GameEngine.field_generator.level_pattern import PatternCell
from GameEngine.field_generator.river_generator import RiverGenerator
from GameEngine.field.cell import *
from GameEngine.field.wall import *


class FieldGenerator:
    """
    This is Field generator object

    Its generate game-field with given rules
    """
    def __init__(self, generator_rules: dict):
        self.rows = generator_rules['rows']
        self.cols = generator_rules['cols']
        self.pattern: list[list[PatternCell]] = [[]]
        self.ground_cells: list[Cell] = []
        self.rivers: list[list[CellRiver]] = []
        self.field: list[list[Cell | None]] = [[]]
        self.treasures: list[Treasure] = []
        self.exit_cell: CellExit | None = None
        self._generate_field(rules=generator_rules)

    def get_field(self):
        """returns generated field"""
        return self.field

    def get_treasures(self):
        """returns generated treasures"""
        return self.treasures

    def get_exit_cell(self):
        """returns generated exit-cell"""
        return self.exit_cell

    def _generate_field(self, rules):
        self._generate_pattern(rules['is_rect'])
        self._generate_base_field()
        self.rivers = self._generate_rivers(rules['river_rules'])
        self._generate_armory(rules['armory'])
        self._generate_clinic()
        self.treasures = self._spawn_treasures(rules['treasures'])
        self._generate_connections()
        outer_cells = self._generate_outer_walls()
        self._generate_walls(rules['walls'])
        self.exit_cell = self._create_exit(outer_cells)

    def _generate_pattern(self, is_rect: bool):
        """
        Создает форму уровня
        """
        self.pattern = [[PatternCell(col, row) for col in range(self.cols)] for row in range(self.rows)]
        if not is_rect:  # todo это заглушка. нужна функция превращающая прямоугольник в облачко с дырками
            self.pattern[3][0].is_not_none = False
            self.pattern[3][3].is_not_none = False
            self.pattern[3][4].is_not_none = False
            self.pattern[1][2].is_not_none = False

    def _generate_base_field(self):
        self.field = [[Cell(col, row) if self.pattern[row][col].is_not_none else None
                       for col in range(self.cols)] for row in range(self.rows)]

        ground_cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                if type(self.field[row][col]) == Cell:
                    ground_cells.append(self.field[row][col])
        self.ground_cells = ground_cells

    def _generate_rivers(self, river_rules: list[int]):
        rg = RiverGenerator(self.cols, self.rows, self.pattern, self.field, self.ground_cells)
        return rg.spawn_rivers(river_rules)

    def _generate_armory(self, armory_rules: bool):
        """
        :param armory_rules: True if needed 2 different types
        """
        if armory_rules:
            cell = choice(self.ground_cells)
            self.field[cell.y][cell.x] = CellArmoryWeapon(cell.x, cell.y)
            self.ground_cells.remove(cell)
            cell = choice(self.ground_cells)
            self.field[cell.y][cell.x] = CellArmoryExplosive(cell.x, cell.y)
            self.ground_cells.remove(cell)
        else:
            cell = choice(self.ground_cells)
            self.field[cell.y][cell.x] = CellArmory(cell.x, cell.y)
            self.ground_cells.remove(cell)

    def _generate_clinic(self):
        cell = choice(self.ground_cells)
        self.field[cell.y][cell.x] = CellClinic(cell.x, cell.y)
        self.ground_cells.remove(cell)

    def _generate_connections(self):
        for row in range(0, self.rows):
            for col in range(0, self.cols):
                if self.field[row][col] is not None:
                    neighbours = {}
                    for direction in Directions:
                        x, y = direction.calc(col, row)
                        if x in range(self.cols) and y in range(self.rows) and isinstance(self.field[y][x], Cell):
                            neighbours.update({direction: self.field[y][x]})
                        else:
                            neighbours.update({direction: None})

                    self.field[row][col].change_neighbours(neighbours)

    def _generate_walls(self, wall_rules):  # todo
        if not wall_rules.get('has_walls'):
            return
        cells = []
        for row in self.field:
            for cell in row:
                if cell:
                    cells.append(cell)
        cells_walls = sample(cells, int(len(cells) * 0.6))
        for cell in cells_walls:
            directions = sample(list(Directions), randint(1, 2))
            for direction in directions:
                if not isinstance(cell.walls[direction], WallOuter):
                    cell.add_wall(direction, WallConcrete())
                    cell.neighbours[direction].add_wall(-direction, WallConcrete())
        self._wall_fix()

    def _wall_fix(self):
        for river in self.rivers:
            for i in range(len(river)-1):
                direction = river[i] - river[i+1]
                river[i].break_wall(direction)

    def _generate_outer_walls(self):
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
    def _create_exit(outer_cells):
        cell = choice(outer_cells)
        dirs = []
        for direction in Directions:
            if isinstance(cell.walls[direction], WallOuter):
                dirs.append(direction)
        direction = choice(dirs)
        cell.add_wall(direction, WallExit())
        exit_cell = CellExit(*direction.calc(cell.x, cell.y), -direction, cell)
        cell.neighbours.update({direction: exit_cell})
        return exit_cell

    def _spawn_treasures(self, treasures_rules: list[int]):
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
