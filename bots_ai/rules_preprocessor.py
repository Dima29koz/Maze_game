from typing import Type

from GameEngine.field import cell, wall
from bots_ai.field_obj import UnknownCell, UnbreakableWall, UnknownWall, NoneCell


class RulesPreprocessor:
    def __init__(self, game_rules: dict):
        self._rules = game_rules
        self.exit_location = self._get_exit_location()

    def _get_exit_location(self):
        if self._rules.get('generator_rules').get('is_not_rect'):
            return [NoneCell, UnknownCell]
        return [NoneCell]

