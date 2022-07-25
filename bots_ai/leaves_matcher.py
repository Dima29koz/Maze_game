from copy import deepcopy
from typing import Type

from GameEngine.field import cell
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState
from bots_ai.exceptions import MatchingError


class LeavesMatcher:
    def __init__(self,
                 unique_objs_amount: dict[Type[cell.Cell], int],
                 players_roots: dict[str, FieldState]):
        self._unique_objs_amount = unique_objs_amount
        self._players_roots = players_roots

    def match_real_spawn_leaves(self, active_player: str):
        active_player_nodes = self._get_player_real_spawn_leaves(active_player)
        other_players = list(self._players_roots.keys())
        other_players.remove(active_player)
        if not other_players:
            return

        other_players_nodes: dict[str, list[FieldState]] = {
            player: self._get_player_compatible_leaves(player, active_player) for player in other_players}
        for node in active_player_nodes[::-1]:
            try:
                self._match_node(node, other_players_nodes, active_player)
            except MatchingError:
                if node.is_real:  # todo for testing
                    for row in node.field:
                        print(row)
                node.remove()

    def _get_player_leaves(self, player_name: str) -> list[FieldState]:
        return self._players_roots.get(player_name).get_leaf_nodes()

    def _get_player_real_spawn_leaves(self, player_name: str) -> list[FieldState]:
        return self._players_roots.get(player_name).get_real_spawn_leaves()

    def _get_player_compatible_leaves(self, player_name: str, target_player: str) -> list[FieldState]:
        leaves = self._players_roots.get(player_name).get_compatible_leaves(target_player)
        [leaf.update_compatibility(target_player, False) for leaf in leaves]
        return leaves

    def _match_node(self, node: FieldState,
                    other_players: dict[str, list[FieldState]], active_player: str):
        for player in other_players:
            matchable_nodes = self._match_with_player(node.field, other_players[player], active_player)
            if not matchable_nodes:
                raise MatchingError()
            if len(matchable_nodes) == 1:
                print('matching')
                for i, row in enumerate(node.field):
                    print(row, matchable_nodes[0].field[i])

                self.join_nodes(node, matchable_nodes[0])

    def _match_with_player(self, field: list[list[cell.Cell | cell.CellRiver | None]],
                           other_nodes: list[FieldState], active_player: str):
        matchable_nodes = []
        for pl_node in other_nodes[::-1]:
            if self._is_matchable(field, pl_node.field):
                matchable_nodes.append(pl_node)
                pl_node.update_compatibility(active_player, True)
        return matchable_nodes

    def _is_matchable(self, field: list[list[cell.Cell | cell.CellRiver | None]],
                      other_field: list[list[cell.Cell | cell.CellRiver | None]]):
        unique_objs = self._unique_objs_amount.copy()
        for y, row in enumerate(field):
            for x, self_cell in enumerate(row):
                other_cell = other_field[y][x]
                if self_cell is None and other_cell is None:
                    continue
                if other_cell is None and type(self_cell) is cell.CellExit:
                    continue
                if self_cell is None and type(other_cell) is cell.CellExit:
                    continue

                if type(other_cell) is UnknownCell:
                    if unique_objs.get(type(self_cell)) is not None:
                        if unique_objs.get(type(self_cell)) > 0:
                            unique_objs[type(self_cell)] -= 1
                        else:
                            return False
                    continue
                if type(self_cell) is UnknownCell:
                    if unique_objs.get(type(other_cell)) is not None:
                        if unique_objs.get(type(other_cell)) > 0:
                            unique_objs[type(other_cell)] -= 1
                        else:
                            return False
                    continue

                if type(other_cell) is type(self_cell):
                    if unique_objs.get(type(self_cell)) is not None:
                        if unique_objs.get(type(self_cell)) > 0:
                            unique_objs[type(self_cell)] -= 1
                        else:
                            return False
                    if type(other_cell) is cell.CellRiver:
                        if other_cell.direction is not self_cell.direction:
                            return False
                    continue
                else:
                    return False
        return True

    def join_nodes(self, node: FieldState, other_node: FieldState):
        for y, row in enumerate(node.field):
            for x, cell_obj in enumerate(row):
                other_cell = other_node.field[y][x]
                if cell_obj is None and other_cell is not None:
                    node.field[y][x] = deepcopy(other_cell)
                    continue
                if type(cell_obj) is UnknownCell and type(other_cell) is not UnknownCell:
                    walls = node.field[y][x].walls
                    node.field[y][x] = deepcopy(other_cell)
                    node.field[y][x].walls = walls
                    continue
