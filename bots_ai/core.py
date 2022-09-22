from GameEngine.field import cell
from GameEngine.globalEnv.enums import Directions, Actions
from GameEngine.globalEnv.types import Position
from bots_ai.decision_making.decision_maker import DecisionMaker
from bots_ai.initial_generator import InitGenerator
from bots_ai.leaves_matcher import LeavesMatcher
from bots_ai.field_handler.player_state import PlayerState
from bots_ai.utils import is_node_is_real, is_node_is_valid


class BotAI:
    def __init__(self, game_rules: dict, players: dict[str, Position]):
        init_generator = InitGenerator(game_rules, players)
        self.players: dict[str, PlayerState] = {
            player_name: PlayerState(init_generator.get_start_state(player_name),
                                     init_generator.rules_preprocessor,
                                     player_name)
            for player_name in players.keys()}
        self.leaves_matcher = LeavesMatcher(init_generator.get_unique_obj_amount(), self.players)
        self.decision_maker = DecisionMaker(game_rules, self.players)

        self.real_field: list[list[cell.Cell | None]] = []

    def turn_prepare(self, player_name: str):
        # before decision-making:
        # удалить все свои листы с правильным спавном, которые противоречат листам противников
        self.leaves_matcher.match_real_spawn_leaves(player_name)
        if not self.has_real_field(player_name):
            print(f'{player_name} matcher err!!!')

    def make_decision(self, player_name: str) -> tuple[Actions, Directions | None]:
        return self.decision_maker.make_decision(player_name)

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')
        for player in self.players:
            self.players.get(player).process_turn(player_name, action, direction, response)

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
            cropped_field = [row[1:-1] for row in node.field.get_field()[1:-1]]
            if is_node_is_real(cropped_field, [row[1:-1] for row in self.real_field[1:-1]]):
                node.is_real = True  # todo
                flag = True
        return flag

    def get_spawn_amount(self, player_name: str):
        return len(self.players.get(player_name).root.next_states)

    def has_bad_nodes(self, player_name: str):
        for node in self.players.get(player_name).get_leaf_nodes():
            if not is_node_is_valid(node):
                for row in node.field:
                    print(row)
                return True
        return False


if __name__ == "__main__":
    pass
