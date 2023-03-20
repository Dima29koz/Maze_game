from random import seed

from ..field.game_map import GameMap
from .field_generator import FieldGenerator
from ..entities.treasure import Treasure
from .level_pattern import LevelPattern
from ..field.cell import (
    CellExit)
from ..global_env.types import LevelPosition


class MapGenerator:
    """
    This is Map generator object

    Its generate game-map with given rules
    """

    def __init__(self, generator_rules: dict):
        seed(generator_rules['seed'])
        self.generator_rules = generator_rules
        self.rows = self.generator_rules['rows'] + 2
        self.cols = self.generator_rules['cols'] + 2
        self.level_patterns: list[LevelPattern] = []
        self.game_map: GameMap = GameMap()
        self.exit_cells: list[CellExit] = []
        self.treasures: list[Treasure] = []
        self._generate_map()

    def get_map(self):
        return self.game_map

    def get_exit_cells(self):
        return self.exit_cells

    def get_treasures(self):
        return self.treasures

    def _generate_map(self):
        self._generate_patterns()
        self._gen_map()

    def _generate_patterns(self):
        for dim in range(self.generator_rules.get('dimensions_amount', 1)):
            prev_pattern = None
            for level in range(self.generator_rules.get('levels_amount', 1)):
                new_pattern = LevelPattern(prev_pattern, LevelPosition(level, 0, dim), self.generator_rules)
                self.level_patterns.append(new_pattern)
                prev_pattern = new_pattern

    def _gen_map(self):
        for level_pattern in self.level_patterns:
            self._generate_level(level_pattern)

    def _generate_level(self, level_pattern: LevelPattern):
        level_generator = FieldGenerator(self.generator_rules, level_pattern)
        levels = level_generator.get_fields()

        for cell in level_generator.get_exit_cells():
            self.exit_cells.append(cell)
        for treasure in level_generator.get_treasures():
            self.treasures.append(treasure)
        for level in levels:
            self.game_map.game_map.append(level)
