from ...game_engine.global_env.types import Position
from ..exceptions import IncompatibleState
from .field_state import FieldState


class Node:
    def __init__(self, field_state: FieldState,
                 enemy_compatibility: dict[str, bool],
                 is_real_spawn: bool = False,
                 parent: 'Node' = None):
        self.field_state = field_state
        self.enemy_compatibility = enemy_compatibility
        self.is_real_spawn = is_real_spawn
        self._parent: Node | None = parent
        self.next_states: list[Node] = []

        self.is_real = False  # todo debug only

    def get_current_data(self):
        return self.field_state.get_current_data()

    def copy(self, player_position: tuple[str, Position] = None, field_state: FieldState = None) -> 'Node':
        return Node(
            self.field_state.copy(player_position) if not field_state else field_state,
            self.enemy_compatibility.copy(),
            is_real_spawn=self.is_real_spawn,
            parent=self)

    def remove(self):
        self._parent._remove_leaf(self)

    def update_compatibility(self, player_name: str, value: bool):
        self.enemy_compatibility[player_name] = value

    def check_compatibility(self) -> bool:
        if True not in self.enemy_compatibility.values() and not self.is_real_spawn:
            raise IncompatibleState()
        return True

    def set_next_states(self, next_states: list['Node']):
        for state in next_states:
            if state is not self:
                state._set_parent(self)
                self.next_states.append(state)

    def add_next_state(self, field_state: FieldState):
        self.next_states.append(self.copy(field_state=field_state))

    def merge_with(self, other_node: 'Node', other_player: str) -> 'Node':
        merged_node = self.copy()
        merged_node.field_state.merge_with(other_node.field_state, other_player)
        return merged_node

    def _remove_leaf(self, leaf: 'Node'):
        self.next_states.remove(leaf)
        if not self.next_states and self._parent:
            self._parent._remove_leaf(self)

    def _set_parent(self, parent: 'Node'):
        self._parent = parent

    def is_deleted(self) -> bool:
        return self not in self._parent.next_states
