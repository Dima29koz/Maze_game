from typing import Type

from game_engine.field import cell
from bots_ai.field_handler.field_obj import UnknownCell, PossibleExit
from bots_ai.field_handler.grid import CELL
from bots_ai.field_handler.player_stats import PlayerStats


class CommonData:
    def __init__(self, game_rules: dict):
        self._rules = game_rules
        self.exit_location = self._get_exit_location()
        self.compatible_cells = self._get_compatible_cells()
        self.treasures_amount: int = sum(self._rules.get('generator_rules').get('treasures'))
        self.players_with_treasures: int = 0

    def get_player_stats(self):
        return PlayerStats(self._rules)

    def _get_exit_location(self) -> list[Type[CELL]]:
        if self._rules.get('generator_rules').get('is_not_rect'):
            return [cell.NoneCell, UnknownCell, PossibleExit]
        return [cell.NoneCell, PossibleExit]

    def _get_compatible_cells(self) -> dict[Type[CELL], list[Type[CELL]]]:
        compatible_cells: dict[Type[CELL], list[Type[CELL]]] = {
            cell.Cell: [UnknownCell, cell.Cell],
            cell.CellRiver: [UnknownCell, cell.CellRiver],
            cell.CellRiverMouth: [UnknownCell, cell.CellRiverMouth],
            cell.CellClinic: [UnknownCell, cell.CellClinic],
            cell.CellArmory: [UnknownCell, cell.CellArmory],
            cell.CellArmoryWeapon: [UnknownCell, cell.CellArmoryWeapon],
            cell.CellArmoryExplosive: [UnknownCell, cell.CellArmoryExplosive],
            cell.CellExit: [cell.CellExit, cell.NoneCell],
            UnknownCell: [
                UnknownCell, cell.Cell, cell.CellRiver,
                cell.CellRiverMouth, cell.CellClinic, cell.CellArmory,
                cell.CellArmoryWeapon, cell.CellArmoryExplosive],
            cell.NoneCell: [cell.NoneCell, cell.CellExit],
        }
        if self._rules.get('generator_rules').get('is_not_rect'):
            compatible_cells[cell.CellExit].append(UnknownCell)
            compatible_cells[UnknownCell].append(cell.CellExit)
            compatible_cells[UnknownCell].append(cell.NoneCell)
            compatible_cells[cell.NoneCell].append(UnknownCell)

        return compatible_cells
