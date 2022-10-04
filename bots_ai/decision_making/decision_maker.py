from random import randint
from GameEngine.globalEnv.enums import Actions, Directions
from bots_ai.decision_making.target_calculator import TargetCalculator
from bots_ai.field_handler.player_state import PlayerState


class DecisionMaker:
    def __init__(self, game_rules: dict, players: dict[str, PlayerState]):
        self.game_rules = game_rules
        self.players = players

    def make_decision(self, player_name: str) -> tuple[Actions, Directions | None]:
        """Среднее первое действие по всем настоящим листам игрока"""
        current_player = self.players.get(player_name)
        player_leaves = current_player.get_real_spawn_leaves()
        first_actions: dict[tuple[Actions, Directions | None], int] = {}
        for leaf in player_leaves:
            graph = leaf.field_state.get_graph(player_name)
            target_calc = TargetCalculator(graph)
            target_cell = target_calc.get_target()
            act = graph.get_first_act(target_cell)
            if act not in first_actions:
                first_actions |= {act: 0}
            first_actions[act] += 1
        return self.calc_avg_action(first_actions)

    def calc_avg_action(self,
                        first_actions: dict[tuple[Actions, Directions | None], int]
                        ) -> tuple[Actions, Directions | None]:
        first_actions_list = sorted(list(first_actions.items()), key=lambda item: -item[1])
        # print(first_actions_list)
        return first_actions_list[0][0]

