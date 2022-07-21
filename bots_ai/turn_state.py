from copy import copy

from GameEngine.field import cell
from GameEngine.globalEnv.enums import Directions, Actions
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState


class BotAI:
    def __init__(self, game_rules: dict, name: str, pos_x: int = None, pos_y: int = None):
        self.size_x = game_rules.get('generator_rules').get('cols')
        self.size_y = game_rules.get('generator_rules').get('rows')
        self.cols = 2 * self.size_x + 1 if pos_x is None else self.size_x + 2
        self.rows = 2 * self.size_y + 1 if pos_y is None else self.size_y + 2
        self.pos_x = pos_x if pos_x is not None else self.size_x
        self.pos_y = pos_y if pos_y is not None else self.size_y
        is_final_size = True if pos_x is not None and pos_y is not None else False
        field = self._generate_start_field()
        self.field_objects_amount: dict = self._get_field_objects_amount(game_rules)
        self.field_root = FieldState(
            field, self.pos_x, self.pos_y, None, copy(self.field_objects_amount),
            self.pos_x, self.pos_x, self.pos_y, self.pos_y,
            self.size_x, self.size_y, self.pos_x, self.pos_y, is_final_size)

    def get_fields(self) -> list[tuple[list[list[cell.Cell | None]], dict[str, int]]]:
        """returns all leaves data of a tree"""
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.field_root, leaves)
        return [leaf.get_current_data() for leaf in leaves]

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')

        for node in self._get_leaf_nodes()[::-1]:
            node.process_action(action, direction, response)

    def has_real_field(self, field: list[list[cell.Cell | None]]):
        for node in self._get_leaf_nodes():
            if self.is_node_is_real(node.field, field):
                node.is_real = True
                return True
        return False

    @staticmethod
    def is_node_is_real(
            n_field: list[list[cell.Cell | cell.CellRiver | None]],
            field: list[list[cell.Cell | cell.CellRiver | None]]):
        for y, row in enumerate(field):
            for x, obj in enumerate(row):
                target_cell = n_field[y][x]
                if obj is None and target_cell is None:
                    continue
                if target_cell is None and type(obj) is cell.CellExit:
                    continue
                if type(target_cell) is UnknownCell:
                    continue
                if type(target_cell) is type(obj):
                    if type(target_cell) is cell.CellRiver:
                        idx = obj.river.index(obj)
                        if target_cell.direction is not obj - obj.river[idx + 1]:
                            return False
                    continue
                else:
                    return False
        return True

    @staticmethod
    def _get_field_objects_amount(rules: dict):
        obj_amount = {
            cell.CellClinic: 1,
            cell.CellArmory: 1,
        }
        return obj_amount

    def _collect_leaf_nodes(self, node: FieldState, leaves: list[FieldState]):
        if node is not None:
            if not node.next_states:
                leaves.append(node)
            for n in node.next_states:
                self._collect_leaf_nodes(n, leaves)

    def _get_leaf_nodes(self) -> list[FieldState]:
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.field_root, leaves)
        return leaves

    def _generate_start_field(self):
        field = [[UnknownCell(col, row)
                  if row not in [0, self.rows - 1] and col not in [0, self.cols - 1] else None
                  for col in range(self.cols)] for row in range(self.rows)]
        self._generate_connections(field)
        return field

    def _generate_connections(self, field):
        for row in range(self.rows):
            for col in range(self.cols):
                if field[row][col] is not None:
                    neighbours = {}
                    for direction in Directions:
                        x, y = direction.calc(col, row)
                        if x in range(self.cols) and y in range(self.rows) and isinstance(field[y][x], cell.Cell):
                            neighbours.update({direction: field[y][x]})
                        else:
                            neighbours.update({direction: None})


if __name__ == "__main__":
    # bot = BotAI(base_rules, '')
    # for row_ in bot.field_root.field:
    #     print(row_)
    pass
