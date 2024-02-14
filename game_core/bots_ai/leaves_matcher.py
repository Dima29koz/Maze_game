from typing import Type

from ..game_engine.field import cell
from ..game_engine.global_env.types import Position
from .field_handler.field_obj import UnknownCell, PossibleExit
from .field_handler.field_state import CELL
from .field_handler.player_state import PlayerState
from .exceptions import MatchingError, MergingError
from .field_handler.tree_node import Node

MAX_MATCHABLE_NODES = 8


class LeavesMatcher:
    def __init__(self,
                 unique_objs_amount: dict[Type[cell.Cell], int],
                 players: dict[str, PlayerState]):
        self._unique_objs_amount = unique_objs_amount
        self._players = players
        self._set_init_compatible_nodes()

    def _set_init_compatible_nodes(self):
        for player, state in self._players.items():
            player_nodes = self._get_player_real_spawn_leaves(player)
            other_players = list(self._players.keys())
            other_players.remove(player)
            for other_player in other_players:
                leaves = self._players[other_player].get_leaf_nodes()
                for node in player_nodes:
                    node.compatible_with[other_player] = leaves

    def match_real_spawn_leaves(self, active_player: str):
        active_player_nodes = self._get_player_real_spawn_leaves(active_player)
        other_players = list(self._players.keys())
        other_players.remove(active_player)
        if not other_players:
            return

        for node in active_player_nodes[::-1]:
            try:
                final_nodes: list[Node] = []
                other_players_nodes = [
                    (player, self._get_node_compatible_leaves(node, player, active_player))
                    for player in other_players
                ]
                self._match_node(node, other_players_nodes, active_player, final_nodes)
                if not final_nodes:
                    node.remove()
                    continue
                node.set_next_states(final_nodes)
            except MatchingError:
                node.remove()

    def _get_player_real_spawn_leaves(self, player_name: str) -> list[Node]:
        return self._players.get(player_name).get_real_spawn_leaves()

    def _get_player_compatible_leaves(self, player_name: str, target_player: str) -> list[Node]:
        leaves = self._players.get(player_name).get_compatible_leaves(target_player)
        [leaf.update_compatibility(target_player, False) for leaf in leaves]
        return leaves

    def _get_node_compatible_leaves(self, node: Node, other_player: str, current_player: str):
        leaves = self._players.get(other_player).get_subtrees_leaf_nodes(node.compatible_with[other_player])
        if not leaves:
            raise MatchingError
        [leaf.update_compatibility(current_player, False) for leaf in leaves]
        return leaves

    def _match_node(self, node: Node,
                    other_players: list[tuple[str, list[Node]]],
                    active_player: str,
                    final_nodes):
        player_name, pl_nodes = other_players.pop()
        merged_nodes = self.merge_node_with_player(node, pl_nodes, active_player, player_name)

        if not other_players:
            final_nodes += merged_nodes
            return
        for merged_node in merged_nodes:
            self._match_node(merged_node, other_players.copy(), active_player, final_nodes)

    def merge_node_with_player(self, node: Node, other_pl_nodes: list[Node],
                               active_pl_name: str, other_pl_name: str) -> list[Node]:
        """

        :param node: node to be merged
        :param other_pl_nodes: nodes for merging
        :param active_pl_name:
        :param other_pl_name:
        :return: list of merged nodes
        :raises MatchingError: if node is not matchable with other player nodes
        """

        if node.field_state.players_positions.get(other_pl_name):
            return [node]
        # node еще не содержит инфы о player
        matchable_nodes = self._match_with_player(node, other_pl_nodes, active_pl_name)
        node.compatible_with[other_pl_name] = matchable_nodes
        if not matchable_nodes:
            # todo raise MatchingError but did not work with it
            return []
        if len(matchable_nodes) > MAX_MATCHABLE_NODES:
            # print('len of matched nodes is:', len(matchable_nodes))
            return [node]

        merged_nodes: list[Node] = []
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

    def _match_with_player(self, node: Node,
                           other_nodes: list[Node], active_player: str):
        matchable_nodes = []
        for pl_node in other_nodes[::-1]:
            if self._is_nodes_matchable(node, pl_node):
                matchable_nodes.append(pl_node)
                pl_node.update_compatibility(active_player, True)
        return matchable_nodes

    def _is_nodes_matchable(self, node: Node, other_node: Node):
        field = node.field_state.field.get_field()
        unique_objs = self._unique_objs_amount.copy()
        for y in range(len(field)):
            for x in range(len(field[0])):
                if not self._is_cells_matchable(node, other_node, x, y, unique_objs):
                    return False
        return True

    @staticmethod
    def _is_cells_matchable(node: Node, other_node: Node,
                            x: int, y: int, unique_objs: dict[Type[CELL], int]):
        self_cell = node.field_state.field.get_cell(Position(x, y))
        other_cell = other_node.field_state.field.get_cell(Position(x, y))
        self_type = type(self_cell)
        other_type = type(other_cell)

        if self_type is cell.NoneCell and other_type in [cell.NoneCell, PossibleExit]:
            return True
        if self_type is cell.CellExit and other_type in [cell.CellExit, PossibleExit]:
            return True
        if self_type is PossibleExit and other_type in [cell.CellExit, cell.NoneCell, PossibleExit]:
            return True
        if self_type is UnknownCell:
            if other_type is UnknownCell:
                return True
            if other_type in unique_objs:
                if unique_objs.get(other_type) > 0:
                    unique_objs[other_type] -= 1
                else:
                    return False
            if other_type is cell.CellRiver:
                if not node.field_state.field.is_river_direction_available(self_cell, other_cell.direction,
                                                                           no_raise=True):
                    return False
            return True

        if other_type is UnknownCell:
            if self_type in unique_objs:
                if unique_objs.get(self_type) > 0:
                    unique_objs[self_type] -= 1
                else:
                    return False
            if self_type is cell.CellRiver:
                if not other_node.field_state.field.is_river_direction_available(other_cell, self_cell.direction,
                                                                                 no_raise=True):
                    return False
            return True

        if self_type is other_type:
            if self_type in unique_objs:
                if unique_objs.get(self_type) > 0:
                    unique_objs[self_type] -= 1
                else:
                    return False
            if other_type is cell.CellRiver:
                if other_cell.direction is not self_cell.direction:
                    return False
            return True

        return False
