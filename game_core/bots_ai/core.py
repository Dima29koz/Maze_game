from ..game_engine.field import cell
from ..game_engine.global_env.enums import Directions, Actions
from ..game_engine.global_env.types import Position
from .decision_making.decision_maker import DecisionMaker
from .initial_generator import InitGenerator
from .leaves_matcher import LeavesMatcher
from .player_iterator import PlayerIterator
from .field_handler.player_state import PlayerState
from .utils import is_node_is_real


class BotAI:
    def __init__(self, game_rules: dict, players: dict[str, Position]):
        init_generator = InitGenerator(game_rules, players)
        self.players: dict[str, PlayerState] = {
            player_name: PlayerState(init_generator.get_start_state(player_name),
                                     init_generator.common_data,
                                     player_name)
            for player_name in players.keys()}
        self.leaves_matcher = LeavesMatcher(init_generator.get_unique_obj_amount(), self.players, game_rules)
        self.decision_maker = DecisionMaker(game_rules, self.players)
        self._player_iter = PlayerIterator(self.players)
        self._common_data = init_generator.common_data

    def turn_prepare(self, player_name: str, player_abilities: dict[Actions, bool]):
        # before decision-making:
        # добавить клад под игроком если его там нет, но действие `swap_treasure` доступно
        for name, player_state in self.players.items():
            player_state.preprocess_turn(player_name, player_abilities)
        # удалить все свои листы с правильным спавном, которые противоречат листам противников
        self.leaves_matcher.match_real_spawn_leaves(player_name)

    def make_decision(self, player_name: str,
                      player_abilities: dict[Actions, bool]) -> tuple[Actions, Directions | None]:
        self.turn_prepare(player_name, player_abilities)
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

        if action is not Actions.swap_treasure:
            next(self._player_iter)
        if self._player_iter.is_host_turn:
            for player_state in self.players.values():
                player_state.process_host_turn()
            self._player_iter.is_host_turn = False


class BotAIDebug(BotAI):
    def __init__(self, game_rules: dict, players: dict[str, Position]):
        super().__init__(game_rules, players)
        self.real_field: list[list[cell.Cell | None]] = []

    def turn_prepare(self, player_name: str, player_abilities: dict[Actions, bool]):
        # before decision-making:
        # удалить все свои листы с правильным спавном, которые противоречат листам противников
        super().turn_prepare(player_name, player_abilities)

        for name, player_state in self.players.items():
            if not self.has_real_field(name):
                print(f'{name} matcher err!!!')

    def process_turn_resp(self, raw_response: dict):
        super().process_turn_resp(raw_response)

        for name, player_state in self.players.items():
            if not self.has_real_field(name):
                print(f'{name} proc err!!!')

    def has_real_field(self, player_name: str):
        if not len(self.players.get(player_name)._root.next_states):
            return False
        flag = False
        for node in self.players.get(player_name).get_leaf_nodes():
            cropped_field = [row[1:-1] for row in node.field_state.field.get_field()[1:-1]]
            if is_node_is_real(
                    cropped_field,
                    [row[1:-1] for row in self.real_field[1:-1]],
                    self.leaves_matcher._unique_objs_amount.copy()):
                node.is_real = True
                flag = True
            else:
                node.is_real = False
        return flag
