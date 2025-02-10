from .field_obj import BotCellTypes
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

    def _get_exit_location(self) -> list[BotCellTypes]:
        if self._rules.get('generator_rules').get('is_not_rect'):
            return [BotCellTypes.NoneCell, BotCellTypes.UnknownCell, BotCellTypes.PossibleExit]
        return [BotCellTypes.NoneCell, BotCellTypes.PossibleExit]

    def _get_compatible_cells(self) -> dict[BotCellTypes, list[BotCellTypes]]:
        compatible_cells: dict[BotCellTypes, list[BotCellTypes]] = {
            BotCellTypes.Cell: [BotCellTypes.UnknownCell, BotCellTypes.Cell],
            BotCellTypes.CellRiver: [BotCellTypes.UnknownCell, BotCellTypes.CellRiver],
            BotCellTypes.CellRiverMouth: [BotCellTypes.UnknownCell, BotCellTypes.CellRiverMouth],
            BotCellTypes.CellClinic: [BotCellTypes.UnknownCell, BotCellTypes.CellClinic],
            BotCellTypes.CellArmory: [BotCellTypes.UnknownCell, BotCellTypes.CellArmory],
            BotCellTypes.CellArmoryWeapon: [BotCellTypes.UnknownCell, BotCellTypes.CellArmoryWeapon],
            BotCellTypes.CellArmoryExplosive: [BotCellTypes.UnknownCell, BotCellTypes.CellArmoryExplosive],
            BotCellTypes.CellExit: [BotCellTypes.CellExit, BotCellTypes.NoneCell],
            BotCellTypes.UnknownCell: [
                BotCellTypes.UnknownCell, BotCellTypes.Cell, BotCellTypes.CellRiver,
                BotCellTypes.CellRiverMouth, BotCellTypes.CellClinic, BotCellTypes.CellArmory,
                BotCellTypes.CellArmoryWeapon, BotCellTypes.CellArmoryExplosive],
            BotCellTypes.NoneCell: [BotCellTypes.NoneCell, BotCellTypes.CellExit],
        }
        if self._rules.get('generator_rules').get('is_not_rect'):
            compatible_cells[BotCellTypes.CellExit].append(BotCellTypes.UnknownCell)
            compatible_cells[BotCellTypes.UnknownCell].append(BotCellTypes.CellExit)
            compatible_cells[BotCellTypes.UnknownCell].append(BotCellTypes.NoneCell)
            compatible_cells[BotCellTypes.NoneCell].append(BotCellTypes.UnknownCell)

        return compatible_cells
