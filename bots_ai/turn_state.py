from copy import copy

from GameEngine.field import cell
from GameEngine.globalEnv.enums import Directions, Actions
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState


class BotAI:
    def __init__(self, game_rules: dict, players: list[tuple[dict[str, int | None], str]], known_spawns=False):
        self.size_x: int = game_rules.get('generator_rules').get('cols')
        self.size_y: int = game_rules.get('generator_rules').get('rows')
        self.cols = 2 * self.size_x + 1
        self.rows = 2 * self.size_y + 1
        self.field_objects_amount: dict = self._get_field_objects_amount(game_rules)

        self.field_root = self._get_start_state(players[0], known_spawns)

        self.players_roots = {player[1]: self._get_start_state(player, known_spawns) for player in players}

    def get_fields(self, player_name: str) -> list[tuple[list[list[cell.Cell | None]], dict[str, int]]]:
        """returns all leaves data of a tree"""
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.players_roots.get(player_name), leaves)
        return [leaf.get_current_data() for leaf in leaves]

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')

        for node in self._get_leaf_nodes(player_name)[::-1]:
            node.process_action(action, direction, response)

    def has_real_field(self, field: list[list[cell.Cell | None]], player_name: str):
        for node in self._get_leaf_nodes(player_name):
            for cropped_field in node.get_cropped_fields():
                if self.is_node_is_real(cropped_field, [row[1:-1] for row in field[1:-1]]):
                    node.is_real = True  # todo
                    return True
        return False

    def get_spawn(self, player_name: str):
        node = self._get_leaf_nodes(player_name)[0]
        return node.get_spaw_points()

    def get_cropped_field(self, player_name: str):
        node = self._get_leaf_nodes(player_name)[0]
        fields = node.get_cropped_fields()
        for field in fields:
            for row in field:
                print(row)
            print()

    def has_bad_nodes(self, player_name: str):
        for node in self._get_leaf_nodes(player_name):
            if not self.is_node_is_valid(node):
                for row in node.field:
                    print(row)
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
    def is_node_is_valid(node: FieldState):
        for row in node.field:
            for cell_obj in row:
                if type(cell_obj) is cell.CellRiverMouth:
                    may_have_input = False
                    for direction in Directions:
                        x, y = direction.calc(cell_obj.x, cell_obj.y)
                        neighbour = node.field[y][x]
                        if neighbour:
                            if type(neighbour) is cell.CellRiver and neighbour.direction is -direction:
                                may_have_input = True
                            if type(neighbour) is UnknownCell:
                                may_have_input = True
                    if not may_have_input:
                        return False
        return True

    def _get_start_state(self, player, known_spawns):
        pos_x = player[0].get('x') if known_spawns else None
        pos_y = player[0].get('y') if known_spawns else None
        min_x = self.size_x if pos_x is None else self.size_x - pos_x + 1
        max_x = self.size_x if pos_x is None else 2 * self.size_x - pos_x
        min_y = self.size_y if pos_y is None else self.size_y - pos_y + 1
        max_y = self.size_y if pos_y is None else 2 * self.size_y - pos_y
        name = player[1]

        field = self._generate_start_field(pos_x, pos_y, known_spawns)

        return FieldState(
            field, copy(self.field_objects_amount),
            self.size_x, self.size_y,
            min_x, max_x, min_y, max_y,
            is_final_size=known_spawns)

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

    def _get_leaf_nodes(self, player_name: str) -> list[FieldState]:
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.players_roots.get(player_name), leaves)
        return leaves

    def _generate_start_field(self, pos_x, pos_y, is_final_size):
        if is_final_size:
            none_cols = list(range(1 + self.size_x - pos_x)) + list(range(self.cols - pos_x, self.cols))
            none_rows = list(range(1 + self.size_y - pos_y)) + list(range(self.rows - pos_y, self.rows))
        else:
            none_cols = [0, self.cols - 1]
            none_rows = [0, self.rows - 1]

        field = [[UnknownCell(col, row)
                  if row not in none_rows and col not in none_cols else None
                  for col in range(self.cols)] for row in range(self.rows)]
        return field


if __name__ == "__main__":
    # bot = BotAI(base_rules, '')
    # for row_ in bot.field_root.field:
    #     print(row_)
    pass
