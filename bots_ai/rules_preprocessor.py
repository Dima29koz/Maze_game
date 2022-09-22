from typing import Type

from GameEngine.field import cell
from bots_ai.field_handler.field_obj import UnknownCell, NoneCell
from bots_ai.field_handler.grid import CELL


class RulesPreprocessor:
    def __init__(self, game_rules: dict):
        self._rules = game_rules
        self.exit_location = self._get_exit_location()
        self.compatible_cells = self._get_compatible_cells()

    def _get_exit_location(self):
        if self._rules.get('generator_rules').get('is_not_rect'):
            return [NoneCell, UnknownCell]
        return [NoneCell]

    def _get_compatible_cells(self) -> dict[Type[CELL], list[Type[CELL]]]:
        compatible_cells = {
            cell.Cell: [UnknownCell, cell.Cell],
            cell.CellRiver: [UnknownCell, cell.CellRiver],
            cell.CellRiverMouth: [UnknownCell, cell.CellRiverMouth],
            cell.CellClinic: [UnknownCell, cell.CellClinic],
            cell.CellArmory: [UnknownCell, cell.CellArmory],
            cell.CellArmoryWeapon: [UnknownCell, cell.CellArmoryWeapon],
            cell.CellArmoryExplosive: [UnknownCell, cell.CellArmoryExplosive],
            cell.CellExit: [cell.CellExit, NoneCell],
            UnknownCell: [
                UnknownCell, cell.Cell, cell.CellRiver,
                cell.CellRiverMouth, cell.CellClinic, cell.CellArmory,
                cell.CellArmoryWeapon, cell.CellArmoryExplosive],
            NoneCell: [NoneCell, cell.CellExit],
        }
        if self._rules.get('generator_rules').get('is_not_rect'):
            compatible_cells[cell.CellExit].append(UnknownCell)
            compatible_cells[UnknownCell].append(cell.CellExit)
            compatible_cells[UnknownCell].append(NoneCell)
            compatible_cells[NoneCell].append(UnknownCell)

        return compatible_cells
