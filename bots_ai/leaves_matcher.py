from copy import deepcopy
from typing import Type

from GameEngine.field import cell
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState, CELL, WALL
from bots_ai.player_state import PlayerState
from bots_ai.exceptions import MatchingError, MergingError


class LeavesMatcher:
    def __init__(self,
                 unique_objs_amount: dict[Type[cell.Cell], int],
                 players: dict[str, PlayerState]):
        self._unique_objs_amount = unique_objs_amount
        self._players = players

    def match_real_spawn_leaves(self, active_player: str):
        active_player_nodes = self._get_player_real_spawn_leaves(active_player)
        other_players = list(self._players.keys())
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
        return self._players.get(player_name).get_leaf_nodes()

    def _get_player_real_spawn_leaves(self, player_name: str) -> list[FieldState]:
        return self._players.get(player_name).get_real_spawn_leaves()

    def _get_player_compatible_leaves(self, player_name: str, target_player: str) -> list[FieldState]:
        leaves = self._players.get(player_name).get_compatible_leaves(target_player)
        [leaf.update_compatibility(target_player, False) for leaf in leaves]
        return leaves

    def _match_node(self, node: FieldState,
                    other_players: dict[str, list[FieldState]], active_player: str):
        for player in other_players:
            matchable_nodes = self._match_with_player(node, other_players[player], active_player)
            if not matchable_nodes:
                raise MatchingError()
            if len(matchable_nodes) > 8:
                print('len of matched nodes is:', len(matchable_nodes))
                return

            if len(matchable_nodes) == 1:
                print('matching 1 time')
                try:
                    merged_node = node.copy().merge_with(matchable_nodes[0])
                    if merged_node:
                        node.field = merged_node.field
                except MergingError:
                    matchable_nodes[0].update_compatibility(active_player, False)

            else:
                print('matching less then 8 times')
                for matchable_node in matchable_nodes:
                    merged_node = node.copy().merge_with(matchable_node)
                    if merged_node:
                        node.next_states.append(merged_node)

    def _match_with_player(self, node: FieldState,
                           other_nodes: list[FieldState], active_player: str):
        matchable_nodes = []
        for pl_node in other_nodes[::-1]:
            if self._is_nodes_matchable(node, pl_node):
                matchable_nodes.append(pl_node)
                pl_node.update_compatibility(active_player, True)
        return matchable_nodes

    def _is_nodes_matchable(self, node: FieldState, other_node: FieldState):
        field = node.field
        unique_objs = self._unique_objs_amount.copy()
        for y in range(len(field)):
            for x in range(len(field[0])):
                if not self._is_cells_matchable(node, other_node, x, y, unique_objs):
                    return False
        return True

    def _is_cells_matchable(self, node: FieldState, other_node: FieldState,
                            x: int, y: int, unique_objs: dict[Type[CELL], int]):
        self_cell = node.field[y][x]
        other_cell = other_node.field[y][x]

        if self_cell is None and (other_cell is None or type(other_cell) is cell.CellExit):
            return True
        if type(self_cell) is cell.CellExit and other_cell is None:
            return True
        if type(self_cell) is UnknownCell:
            if type(other_cell) is UnknownCell:
                return True
            if type(other_cell) in unique_objs:
                if unique_objs.get(type(other_cell)) > 0:
                    unique_objs[type(other_cell)] -= 1
                else:
                    return False
            if type(other_cell) is cell.CellRiver:
                if not node.is_river_direction_available(self_cell, other_cell.direction, no_raise=True):
                    return False
            return True

        if type(other_cell) is UnknownCell:
            if unique_objs.get(type(self_cell)) is not None:
                if unique_objs.get(type(self_cell)) > 0:
                    unique_objs[type(self_cell)] -= 1
                else:
                    return False
            if type(self_cell) is cell.CellRiver:
                if self_cell.direction not in other_node.get_possible_river_directions(other_cell):
                    return False
            return True

        if type(self_cell) is type(other_cell):
            if type(self_cell) in unique_objs:
                if unique_objs.get(type(self_cell)) > 0:
                    unique_objs[type(self_cell)] -= 1
                else:
                    return False
            if type(other_cell) is cell.CellRiver:
                if other_cell.direction is not self_cell.direction:
                    return False
            return True

        return False

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
