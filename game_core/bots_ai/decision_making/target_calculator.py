from .graph_builder import GraphBuilder
from ..field_handler.field_obj import (
    CellClinic, CellArmoryWeapon, CellArmoryExplosive,
    CellArmory, CellExit, UnknownCell, PossibleExit
)
from ..field_handler.field_state import FieldState
from ..field_handler.grid import CELL
from ..field_handler.player_stats import PlayerStats
from ...game_engine.global_env.enums import Actions


class TargetCalculator:
    def __init__(self, current_player_name: str,
                 players_stats: dict[str, PlayerStats]):
        self.current_player_name = current_player_name
        self.cur_pl_stats = players_stats.get(self.current_player_name)
        self.other_players_stats = players_stats
        self.other_players_stats.pop(self.current_player_name)

    def get_target(self, graph: GraphBuilder, field_state: FieldState) -> CELL:
        res = []
        cell_weight = {
            UnknownCell: 10,
            PossibleExit: 7 if not self.cur_pl_stats.has_treasure else 12,
            CellClinic: 8 if self.cur_pl_stats.health < self.cur_pl_stats.health_max else 1,
            CellArmoryWeapon: 2 * (self.cur_pl_stats.arrows_max - self.cur_pl_stats.arrows),
            CellArmoryExplosive: 2 * (self.cur_pl_stats.bombs_max - self.cur_pl_stats.bombs),
            CellArmory: (
                    self.cur_pl_stats.arrows_max - self.cur_pl_stats.arrows +
                    self.cur_pl_stats.bombs_max - self.cur_pl_stats.bombs),
            CellExit: 15 if self.cur_pl_stats.has_treasure else 1,
        }
        for target, path_len in graph.paths_len.items():
            try:
                weight = cell_weight.get(type(target), 1) / path_len
                if target.position in field_state.treasures_positions \
                        and not self.cur_pl_stats.has_treasure \
                        and self.cur_pl_stats.get_allowed_abilities().get(Actions.swap_treasure):
                    weight *= 10
                res.append((target, weight))
            except ZeroDivisionError:
                pass
        res = sorted(res, key=lambda item: -item[1])
        # print(res)
        return res[0][0]
