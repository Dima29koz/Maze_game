from GameEngine.globalEnv.enums import Actions, Directions
from bots_ai.field_state import FieldState


class PlayerState:
    def __init__(self, tree_root: FieldState, name: str):
        self.root = tree_root
        self.name = name

    def process_turn(self, action: Actions, direction: Directions | None, response: dict):
        # before turn processing:
        # делать ход во всех своих листах, которые противники считают возможными,
        # то есть хотя бы 1 противник думает что данный лист возможен
        # и во всех листах с настоящим спавном
        for node in self.get_leaf_nodes()[::-1]:
            if node.check_compatibility():
                node.process_action(action, direction, response)

    def get_leaf_nodes(self):
        """
        :return: list of all leaves of a tree
        """
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.root, leaves)
        return leaves

    def get_real_spawn_leaves(self):
        """
        :return: list of only real-spawn leaves of a tree
        """
        leaves: list[FieldState] = []
        self._collect_real_spawn_nodes(self.root, leaves)
        return leaves

    def get_compatible_leaves(self, target_player: str):
        """
        :return: list of all leaves of a tree which compatible with target player
        """
        leaves: list[FieldState] = []
        self._collect_compatible_nodes(self.root, leaves, target_player)
        return leaves

    def _collect_leaf_nodes(self, node, leaves: list):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            self._collect_leaf_nodes(state, leaves)

    def _collect_real_spawn_nodes(self, node, leaves: list):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            if state.is_real_spawn:
                self._collect_real_spawn_nodes(state, leaves)

    def _collect_compatible_nodes(self, node, leaves: list, target_player: str):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            if state.enemy_compatibility[target_player]:
                self._collect_compatible_nodes(state, leaves, target_player)
