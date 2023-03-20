from random import choice, sample, randint

from ..field.game_level import GameLevel
from ..global_env.enums import Directions
from ..entities.treasure import Treasure, TreasureTypes
from .level_pattern import LevelPattern
from .river_generator import RiverGenerator
from ..field.cell import (
    Cell, CellRiver, CellExit, CellArmory, CellArmoryExplosive, CellArmoryWeapon, CellClinic, NoneCell)
from ..field.wall import *
from ..global_env.types import Position


class FieldGenerator:
    """
    This is Field generator object

    Its generate game-field with given rules
    """

    def __init__(self, generator_rules: dict, pattern: LevelPattern = None):
        self.rows = generator_rules['rows'] + 2
        self.cols = generator_rules['cols'] + 2
        self.pattern = pattern
        self.ground_cells: list[Cell] = []
        self.rivers: list[list[CellRiver]] = []
        self.levels: list[GameLevel] = []
        self.treasures: list[Treasure] = []
        self.exit_cells: list[CellExit] = []
        self._generate_field(rules=generator_rules)

    def get_fields(self) -> list[GameLevel]:
        return self.levels

    def get_treasures(self):
        """returns generated treasures"""
        return self.treasures

    def get_exit_cells(self):
        """returns generated exit-cells"""
        return self.exit_cells

    def _generate_field(self, rules: dict):
        self._generate_base_field()
        self.rivers = self._generate_rivers(rules['river_rules'])
        self._generate_armory(rules['is_separated_armory'])
        self._generate_clinic()
        self.treasures = self._spawn_treasures(rules['treasures'])
        outer_cells = self._generate_outer_walls()
        self._generate_walls(rules['walls'])
        self.exit_cells = self._create_exit(outer_cells, rules['exits_amount'])

    def _is_in_field(self, row: int, col: int) -> bool:
        return row not in [0, self.rows - 1] and col not in [0, self.cols - 1]

    def _generate_base_field(self):
        field = [[
            Cell(Position(col, row, self.pattern.level_position)) if self.pattern.pattern[row][col].is_not_none else
            NoneCell(Position(col, row, self.pattern.level_position))
            for col in range(self.cols)] for row in range(self.rows)]

        level = GameLevel(self.pattern.level_position, field)
        self.levels.append(level)
        ground_cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                if type(level.field[row][col]) == Cell:
                    ground_cells.append(level.field[row][col])
        self.ground_cells = ground_cells

    def _generate_rivers(self, river_rules: dict):
        if not river_rules['has_river']:
            return []
        rg = RiverGenerator(self.cols, self.rows, self.pattern.pattern, self.levels[0].field, self.ground_cells)
        return rg.spawn_rivers(river_rules)

    def _generate_armory(self, is_separated_armory: bool):
        """
        :param is_separated_armory: True if needed 2 different types
        """
        if is_separated_armory:
            cell = choice(self.ground_cells)
            self.levels[0].set_cell(cell.position, CellArmoryWeapon(cell.position))
            self.ground_cells.remove(cell)
            cell = choice(self.ground_cells)
            self.levels[0].set_cell(cell.position, CellArmoryExplosive(cell.position))
            self.ground_cells.remove(cell)
        else:
            cell = choice(self.ground_cells)
            self.levels[0].set_cell(cell.position, CellArmory(cell.position))
            self.ground_cells.remove(cell)

    def _generate_clinic(self):
        cell = choice(self.ground_cells)
        self.levels[0].set_cell(cell.position, CellClinic(cell.position))
        self.ground_cells.remove(cell)

    def _generate_walls(self, wall_rules: dict):
        if not wall_rules.get('has_walls'):
            return
        cells = []
        for row in self.levels[0].field:
            for cell in row:
                if type(cell) is not NoneCell:
                    cells.append(cell)
        cells_walls = sample(cells, int(len(cells) * 0.6))
        for cell in cells_walls:
            directions = sample(list(Directions), randint(1, 2))
            for direction in directions:
                if not isinstance(cell.walls[direction], WallOuter):
                    cell.add_wall(direction, WallConcrete())
                    self.levels[0].get_neighbour_cell(cell.position, direction).add_wall(-direction, WallConcrete())
        self._wall_fix()

    def _wall_fix(self):
        for river in self.rivers:
            for i in range(len(river) - 1):
                direction = river[i] - river[i + 1]
                river[i].direction = direction
                river[i].add_wall(direction, WallEmpty())
                neighbour = self.levels[0].get_neighbour_cell(river[i].position, direction)
                if neighbour:
                    neighbour.add_wall(-direction, WallEmpty())

    def _generate_outer_walls(self) -> list[Cell]:
        outer_cells = []
        for row in self.levels[0].field:
            for cell in row:
                if self._is_cell_outer(cell):
                    outer_cells.append(cell)

        return outer_cells

    def _is_cell_outer(self, cell: Cell):
        if type(cell) is NoneCell:
            return False
        is_outer = False
        for direction in Directions:
            if type(self.levels[0].get_neighbour_cell(cell.position, direction)) is NoneCell:
                cell.add_wall(direction, WallOuter())
                is_outer = True
        return is_outer

    def _create_exit(self, outer_cells: list[Cell], amount: int):
        exit_cells = []
        cells = sample(outer_cells, min(amount, len(outer_cells)))
        for cell in cells:

            dirs = []
            for direction in Directions:
                if isinstance(cell.walls[direction], WallOuter):
                    dirs.append(direction)
            direction = choice(dirs)
            cell.add_wall(direction, WallExit())
            exit_cell = CellExit(cell.position.get_adjacent(direction), -direction)
            exit_cells.append(exit_cell)
            self.levels[0].set_cell(exit_cell.position, exit_cell)
        return exit_cells

    def _spawn_treasures(self, treasures_rules: list[int]):
        treasures = []

        treasure_cells = sample(self.ground_cells, sum(treasures_rules))

        for _ in range(treasures_rules[0]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.very, cell.position))

        for _ in range(treasures_rules[1]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.spurious, cell.position))

        for _ in range(treasures_rules[2]):
            cell = treasure_cells.pop()
            treasures.append(Treasure(TreasureTypes.mined, cell.position))

        return treasures
