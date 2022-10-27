from game_engine.field import cell
from game_engine.global_env.enums import Directions, Actions
from game_engine.global_env.types import Position
from bots_ai.decision_making.decision_maker import DecisionMaker
from bots_ai.initial_generator import InitGenerator
from bots_ai.leaves_matcher import LeavesMatcher
from bots_ai.field_handler.player_state import PlayerState
from bots_ai.utils import is_node_is_real, is_node_is_valid


class BotAI:
    def __init__(self, game_rules: dict, players: dict[str, Position], last_player_name: str):
        init_generator = InitGenerator(game_rules, players)
        self.players: dict[str, PlayerState] = {
            player_name: PlayerState(init_generator.get_start_state(player_name),
                                     init_generator.common_data,
                                     player_name)
            for player_name in players.keys()}
        self.leaves_matcher = LeavesMatcher(init_generator.get_unique_obj_amount(), self.players)
        self.decision_maker = DecisionMaker(game_rules, self.players)
        self._last_player_name = last_player_name
        self._common_data = init_generator.common_data

        self.real_field: list[list[cell.Cell | None]] = []

    def turn_prepare(self, player_name: str):
        # before decision-making:
        # удалить все свои листы с правильным спавном, которые противоречат листам противников
        self.leaves_matcher.match_real_spawn_leaves(player_name)
        if not self.has_real_field(player_name):
            print(f'{player_name} matcher err!!!')

    def make_decision(self, player_name: str,
                      player_abilities: dict[Actions, bool]) -> tuple[Actions, Directions | None]:
        return self.decision_maker.make_decision(player_name, player_abilities)

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')

        if response.get('hit'):
            self._common_data.players_with_treasures -= len(response.get('drop_pls'))
        if response.get('type_out_treasure'):
            self._common_data.players_with_treasures -= 1
            self._common_data.treasures_amount -= 1
        for name, player_state in self.players.items():
            player_state.process_turn(player_name, action, direction, response)

            if not self.has_real_field(name):
                print(f'{name} proc err!!!')
        if player_name == self._last_player_name:
            for player_state in self.players.values():
                player_state.process_host_turn()
        # at the turn end:
        # удалить все свои листы, которые противоречат листам противников,
        # но кажется что это не нужно

    def has_real_field(self, player_name: str):
        if not self.players.get(player_name).get_spawn_amount():
            return False
        flag = False
        for node in self.players.get(player_name).get_leaf_nodes():
            cropped_field = [row[1:-1] for row in node.field_state.field.get_field()[1:-1]]
            if is_node_is_real(cropped_field, [row[1:-1] for row in self.real_field[1:-1]]):
                node.is_real = True  # todo
                flag = True
        return flag


if __name__ == "__main__":
    pass
