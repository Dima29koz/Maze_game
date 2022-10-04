from GameEngine.globalEnv.types import Position
from bots_ai.field_handler.field_state import FieldState


class Node:
    def __init__(self, field_state: FieldState, parent: 'Node' = None):
        self.field_state = field_state
        self.parent: Node | None = parent
        self.next_states: list[Node] = []

    def get_current_data(self):
        return self.field_state.get_current_data()

    def copy(self, player_name: str = None, position: Position = None) -> 'Node':
        return Node(self.field_state.copy(player_name, position), self)

    def remove(self):
        self.parent._remove_leaf(self)

    def _remove_leaf(self, leaf: 'Node'):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent._remove_leaf(self)

    def set_parent(self, parent: 'Node'):
        self.parent = parent

    def set_next_states(self, next_states: list['Node']):
        for state in next_states:
            if state is not self:
                state.set_parent(self)
                self.next_states.append(state)
