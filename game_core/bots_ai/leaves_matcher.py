from typing import Type

from .exceptions import MatchingError, MergingError
from .field_handler.field_obj import (
    CELL, UnknownCell, PossibleExit, NoneCell,
    CellRiver, CellExit
)
from .field_handler.player_state import PlayerState
from .field_handler.tree_node import Node

MAX_MATCHABLE_NODES = 8


class LeavesMatcher:
    def __init__(self,
                 unique_objs_amount: dict[Type[NoneCell], int],
                 players: dict[str, PlayerState],
                 game_rules: dict):
        self._unique_objs_amount = unique_objs_amount
        self._players = players
        self._set_init_compatible_nodes()
        self._size_x: int = game_rules.get('generator_rules').get('cols') + 2
        self._size_y: int = game_rules.get('generator_rules').get('rows') + 2

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
        other_players = [player for player in self._players.keys() if player != active_player]
        if not other_players:
            return

        for player in other_players:
            for leaf in self._players.get(player).get_leaf_nodes():
                leaf.update_compatibility(active_player, False)

        for node in active_player_nodes[::-1]:
            if all(node.field_state.players_positions.values()):
                continue
            self._match_node(node, other_players.copy(), active_player)

    def _get_player_real_spawn_leaves(self, player_name: str) -> list[Node]:
        return self._players.get(player_name).get_real_spawn_leaves()

    def _get_player_compatible_leaves(self, player_name: str, target_player: str) -> list[Node]:
        leaves = self._players.get(player_name).get_compatible_leaves(target_player)
        [leaf.update_compatibility(target_player, False) for leaf in leaves]
        return leaves

    def _get_node_compatible_leaves(self, node: Node, other_player: str) -> list[Node]:
        compatible_roots = node.compatible_with[other_player]
        leaves = self._players.get(other_player).get_subtrees_leaf_nodes(compatible_roots)
        if not leaves:
            raise MatchingError
        return leaves

    def _match_node(self, node: Node, other_players: list[str], active_player: str):
        other_player = other_players.pop()

        merged_nodes = [node]
        # если в листе не известно положение противника
        if not node.field_state.players_positions[other_player]:
            try:
                merged_nodes = self.merge_node_with_player(node, active_player, other_player)
            except MatchingError:
                node.remove()
                return

        if not other_players:
            return
        for merged_node in merged_nodes:
            self._match_node(merged_node, other_players.copy(), active_player)

    def merge_node_with_player(self, node: Node, active_pl_name: str, other_pl_name: str) -> list[Node]:
        """

        :param node: node to be merged
        :param active_pl_name:
        :param other_pl_name:
        :return: list of merged nodes
        :raises MatchingError: if node is not matchable with other player nodes
        """

        other_pl_nodes = self._get_node_compatible_leaves(node, other_pl_name)
        matchable_nodes = self._match_with_player(node, other_pl_nodes)
        node.compatible_with[other_pl_name] = matchable_nodes

        if not matchable_nodes:
            raise MatchingError
        if len(matchable_nodes) > MAX_MATCHABLE_NODES:
            [other_node.update_compatibility(active_pl_name, True) for other_node in matchable_nodes]
            return [node]

        merged_nodes: list[Node] = []
        for matchable_node in matchable_nodes:
            try:
                merged_node = node.merge_with(matchable_node)
                for player in merged_node.compatible_with.keys():
                    player_position = merged_node.field_state.players_positions[player]
                    if player_position:
                        merged_node.compatible_with[player] = None
                merged_nodes.append(merged_node)
            except MergingError:
                pass
        if not merged_nodes:
            raise MatchingError
        node.set_next_states(merged_nodes)
        return merged_nodes

    def _match_with_player(self, node: Node, other_nodes: list[Node]):
        return [pl_node for pl_node in other_nodes if self._is_nodes_matchable(node, pl_node)]

    def _is_nodes_matchable(self, node: Node, other_node: Node):
        for player, position in node.field_state.players_positions.items():
            other_node_player_pos = other_node.field_state.players_positions[player]
            if position and other_node_player_pos and position != other_node_player_pos:
                return False

        unique_objs = self._unique_objs_amount.copy()
        for node_row, other_node_row in zip(node.field_state.field.get_field(),
                                            other_node.field_state.field.get_field()):
            for self_cell, other_cell in zip(node_row, other_node_row):
                if not self._is_cells_matchable(node, other_node, self_cell, other_cell, unique_objs):
                    return False
        return True

    @staticmethod
    def _is_cells_matchable(node: Node, other_node: Node,
                            self_cell, other_cell, unique_objs: dict[Type[CELL], int]):
        self_type = type(self_cell)
        other_type = type(other_cell)

        if self_type is NoneCell and other_type in [NoneCell, PossibleExit]:
            return True
        if self_type is CellExit and other_type in [CellExit, PossibleExit]:
            return True
        if self_type is PossibleExit and other_type in [CellExit, NoneCell, PossibleExit]:
            return True
        if self_type is UnknownCell:
            if other_type is UnknownCell:
                return True
            if other_type in unique_objs:
                if unique_objs.get(other_type) > 0:
                    unique_objs[other_type] -= 1
                else:
                    return False
            if other_type is CellRiver:
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
            if self_type is CellRiver:
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
            if other_type is CellRiver:
                if other_cell.direction is not self_cell.direction:
                    return False
            return True

        return False
