from GameEngine.field import cell
from GameEngine.globalEnv.enums import Directions, Actions
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState
from bots_ai.initial_generator import InitGenerator
from bots_ai.leaves_matcher import LeavesMatcher
from bots_ai.player_state import PlayerState


class BotAI:
    def __init__(self, game_rules: dict, players: list[tuple[dict[str, int | None], str]]):
        self.init_generator = InitGenerator(game_rules, [player[1] for player in players])
        self.players: dict[str, PlayerState] = {
            player[1]: PlayerState(self.init_generator.get_start_state(player), player[1])
            for player in players}
        self.leaves_matcher = LeavesMatcher(self.init_generator.get_unique_obj_amount(), self.players)

        self.real_field: list[list[cell.Cell | None]] = []

    def get_fields(self, player_name: str) -> list[tuple[list[list[cell.Cell | None]], dict[str, int]]]:
        """returns all player leaves data"""
        leaves = self.players.get(player_name).get_leaf_nodes()
        # leaves = self.players.get(player_name).get_real_spawn_leaves()
        return [leaf.get_current_data() for leaf in leaves]

    def turn_prepare(self, player_name: str):
        # before decision-making:
        # удалить все свои листы с правильным спавном, которые противоречат листам противников
        self.leaves_matcher.match_real_spawn_leaves(player_name)
        if not self.has_real_field(player_name):
            print('matcher err!!!')

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')
        self.players.get(player_name).process_turn(action, direction, response)

        if not self.has_real_field(player_name):
            print('proc err!!!')

        # at the turn end:
        # удалить все свои листы, которые противоречат листам противников,
        # но кажется что это не нужно

    def has_real_field(self, player_name: str):
        if not len(self.players.get(player_name).root.next_states):
            return False
        flag = False
        for node in self.players.get(player_name).get_leaf_nodes():
            cropped_field = [row[1:-1] for row in node.field[1:-1]]
            if self.is_node_is_real(cropped_field, [row[1:-1] for row in self.real_field[1:-1]]):
                node.is_real = True  # todo
                flag = True
        return flag

    def get_spawn_amount(self, player_name: str):
        return len(self.players.get(player_name).root.next_states)

    def has_bad_nodes(self, player_name: str):
        for node in self.players.get(player_name).get_leaf_nodes():
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


if __name__ == "__main__":
    pass
