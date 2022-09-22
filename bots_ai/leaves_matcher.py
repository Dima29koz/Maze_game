from typing import Type

from GameEngine.field import cell
from GameEngine.globalEnv.types import Position
from bots_ai.field_handler.field_obj import UnknownCell
from bots_ai.field_handler.field_state import FieldState, CELL
from bots_ai.field_handler.player_state import PlayerState
from bots_ai.exceptions import MatchingError, MergingError

MAX_MATCHABLE_NODES = 8


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

        other_players_nodes: list[tuple[str, list[FieldState]]] = [
            (player, self._get_player_compatible_leaves(player, active_player)) for player in other_players]

        for node in active_player_nodes[::-1]:
            try:
                final_nodes: list[FieldState] = []
                self._match_node(node, other_players_nodes.copy(), active_player, final_nodes)
                if not final_nodes:
                    node.remove()
                    continue
                node.set_next_states(final_nodes)
            except MatchingError:
                node.remove()

    def _get_player_real_spawn_leaves(self, player_name: str) -> list[FieldState]:
        return self._players.get(player_name).get_real_spawn_leaves()

    def _get_player_compatible_leaves(self, player_name: str, target_player: str) -> list[FieldState]:
        leaves = self._players.get(player_name).get_compatible_leaves(target_player)
        [leaf.update_compatibility(target_player, False) for leaf in leaves]
        return leaves

    def _match_node(self, node: FieldState,
                    other_players: list[tuple[str, list[FieldState]]],
                    active_player: str,
                    final_nodes):
        player_name, pl_nodes = other_players.pop()
        merged_nodes = self.merge_node_with_player(node, pl_nodes, active_player, player_name)

        if not other_players:
            final_nodes += merged_nodes
            return
        for merged_node in merged_nodes:
            self._match_node(merged_node, other_players.copy(), active_player, final_nodes)

    def merge_node_with_player(self, node: FieldState, other_pl_nodes: list[FieldState],
                               active_pl_name: str, other_pl_name: str) -> list[FieldState]:
        """

        :param node: node to be merged
        :param other_pl_nodes: nodes for merging
        :param active_pl_name:
        :param other_pl_name:
        :return: list of merged nodes
        :raises MatchingError: if node is not matchable with other player nodes
        """

        if node.players_positions.get(other_pl_name):
            return [node]
        # node еще не содержит инфы о player
        matchable_nodes = self._match_with_player(node, other_pl_nodes, active_pl_name)
        if not matchable_nodes:
            return []
        if len(matchable_nodes) > MAX_MATCHABLE_NODES:
            print('len of matched nodes is:', len(matchable_nodes))
            return [node]

        merged_nodes: list[FieldState] = []
        for matchable_node in matchable_nodes:
            try:
                merged_node = node.merge_with(matchable_node, other_pl_name)
                if merged_node:
                    merged_nodes.append(merged_node)
            except MergingError:
                # matchable_node.update_compatibility(active_pl_name, False)
                # todo bug here можно представить в виде списка листов с которыми матчится
                pass
        if not merged_nodes:
            return []
        return merged_nodes

    def _match_with_player(self, node: FieldState,
                           other_nodes: list[FieldState], active_player: str):
        matchable_nodes = []
        for pl_node in other_nodes[::-1]:
            if self._is_nodes_matchable(node, pl_node):
                matchable_nodes.append(pl_node)
                pl_node.update_compatibility(active_player, True)
        return matchable_nodes

    def _is_nodes_matchable(self, node: FieldState, other_node: FieldState):
        field = node.field.get_field()
        unique_objs = self._unique_objs_amount.copy()
        for y in range(len(field)):
            for x in range(len(field[0])):
                if not self._is_cells_matchable(node, other_node, x, y, unique_objs):
                    return False
        return True

    @staticmethod
    def _is_cells_matchable(node: FieldState, other_node: FieldState,
                            x: int, y: int, unique_objs: dict[Type[CELL], int]):
        self_cell = node.field.get_cell(Position(x, y))
        other_cell = other_node.field.get_cell(Position(x, y))

        if type(self_cell) is cell.NoneCell and type(other_cell) in [cell.CellExit, cell.NoneCell]:
            return True
        if type(self_cell) is cell.CellExit and type(other_cell) is cell.NoneCell:
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
                if not node.field.is_river_direction_available(self_cell, other_cell.direction, no_raise=True):
                    return False
            return True

        if type(other_cell) is UnknownCell:
            if type(self_cell) in unique_objs:
                if unique_objs.get(type(self_cell)) > 0:
                    unique_objs[type(self_cell)] -= 1
                else:
                    return False
            if type(self_cell) is cell.CellRiver:
                if not other_node.field.is_river_direction_available(other_cell, self_cell.direction, no_raise=True):
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
