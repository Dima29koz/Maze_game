from typing import Type

from .field_obj import (
    UnknownCell, PossibleExit, NoneCell,
    Cell, CellRiver, CellRiverMouth,
    CellClinic, CellArmory, CellArmoryWeapon,
    CellArmoryExplosive, CellExit, CELL)
from .player_stats import PlayerStats


class CommonData:
    def __init__(self, game_rules: dict):
        self._rules = game_rules
        self.exit_location = self._get_exit_location()  # fixme
        self.compatible_cells = self._get_compatible_cells()
        self.treasures_amount: int = sum(self._rules.get('generator_rules').get('treasures'))
        self.players_with_treasures: int = 0

    def get_player_stats(self):
        return PlayerStats(self._rules)

    def _get_exit_location(self) -> list[Type[CELL]]:
        if self._rules.get('generator_rules').get('is_not_rect'):
            return [NoneCell, UnknownCell, PossibleExit]
        return [NoneCell, PossibleExit]

    def _get_compatible_cells(self) -> dict[Type[CELL], list[Type[CELL]]]:
        compatible_cells: dict[Type[CELL], list[Type[CELL]]] = {
            Cell: [UnknownCell, Cell],
            CellRiver: [UnknownCell, CellRiver],
            CellRiverMouth: [UnknownCell, CellRiverMouth],
            CellClinic: [UnknownCell, CellClinic],
            CellArmory: [UnknownCell, CellArmory],
            CellArmoryWeapon: [UnknownCell, CellArmoryWeapon],
            CellArmoryExplosive: [UnknownCell, CellArmoryExplosive],
            CellExit: [CellExit, NoneCell],
            UnknownCell: [
                UnknownCell, Cell, CellRiver,
                CellRiverMouth, CellClinic, CellArmory,
                CellArmoryWeapon, CellArmoryExplosive],
            NoneCell: [NoneCell, CellExit],
        }
        if self._rules.get('generator_rules').get('is_not_rect'):
            compatible_cells[CellExit].append(UnknownCell)
            compatible_cells[UnknownCell].append(CellExit)
            compatible_cells[UnknownCell].append(NoneCell)
            compatible_cells[NoneCell].append(UnknownCell)

        return compatible_cells
