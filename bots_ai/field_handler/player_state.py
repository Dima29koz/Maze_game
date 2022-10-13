from typing import Type

from GameEngine.field import cell
from GameEngine.globalEnv.enums import Actions, Directions
from bots_ai.exceptions import UnreachableState, IncompatibleState, MergingError
from bots_ai.field_handler.tree_node import Node
from bots_ai.field_handler.common_data import CommonData


class PlayerState:
    def __init__(self, tree_root: Node, common_data: CommonData, name: str):
        self._root = tree_root
        self.common_data = common_data
        self.name = name
        self.stats = self.common_data.get_player_stats()

    def process_turn(self, player_name: str, action: Actions, direction: Directions | None, response: dict):
        # before turn processing:
        # делать ход во всех своих листах, которые противники считают возможными,
        # то есть хотя бы 1 противник думает что данный лист возможен
        # и во всех листах с настоящим спавном

        self._handle_stats_changes(player_name, action, response)
        for node in self.get_leaf_nodes()[::-1]:
            try:
                if node.check_compatibility():
                    next_states = node.field_state.process_action(player_name, action, direction, response)
                    [node.add_next_state(state) for state in next_states]
            except (UnreachableState, IncompatibleState, MergingError):
                node.remove()

    def _handle_stats_changes(self, player_name: str, action: Actions, response: dict):
        if player_name == self.name:
            type_cell_turn_end: Type[cell.CELL] | None = response.get('type_cell_at_end_of_turn')

            match action:
                case Actions.shoot_bow:
                    self.stats.on_shooting()
                case Actions.throw_bomb:
                    self.stats.on_bombing()
                case Actions.swap_treasure:
                    self.common_data.players_with_treasures += int(self.stats.on_swap_treasure())
                case _:
                    pass

            match type_cell_turn_end:
                case cell.CellClinic:
                    self.stats.restore_heal()
                case cell.CellArmory:
                    self.stats.restore_weapon()
                case cell.CellArmoryExplosive:
                    self.stats.restore_bombs()
                case cell.CellArmoryWeapon:
                    self.stats.restore_arrows()
                case _:
                    pass

        if response.get('hit'):
            dmg_pls: list[str] = response.get('dmg_pls')
            dead_pls: list[str] = response.get('dead_pls')
            drop_pls: list[str] = response.get('drop_pls')
            if self.name in dmg_pls:
                self.common_data.players_with_treasures -= int(self.stats.on_take_dmg())

    def get_spawn_amount(self):
        return len(self._root.next_states)

    def get_leaf_nodes(self):
        """
        :return: list of all leaves of a tree
        """
        leaves: list[Node] = []
        self._collect_leaf_nodes(self._root, leaves)
        return leaves

    def get_real_spawn_leaves(self):
        """
        :return: list of only real-spawn leaves of a tree
        """
        leaves: list[Node] = []
        self._collect_real_spawn_nodes(self._root, leaves)
        return leaves

    def get_compatible_leaves(self, target_player: str):
        """
        :return: list of all leaves of a tree which compatible with target player
        """
        leaves: list[Node] = []
        self._collect_compatible_nodes(self._root, leaves, target_player)
        return leaves

    def _collect_leaf_nodes(self, root: Node, leaves: list[Node]):
        if not root.next_states:
            leaves.append(root)
        for node in root.next_states:
            self._collect_leaf_nodes(node, leaves)

    def _collect_real_spawn_nodes(self, root: Node, leaves: list[Node]):
        if not root.next_states:
            leaves.append(root)
        for node in root.next_states:
            if node.is_real_spawn:
                self._collect_real_spawn_nodes(node, leaves)

    def _collect_compatible_nodes(self, root: Node, leaves: list[Node], target_player: str):
        if not root.next_states:
            leaves.append(root)
        for node in root.next_states:
            if node.enemy_compatibility[target_player]:
                self._collect_compatible_nodes(node, leaves, target_player)
