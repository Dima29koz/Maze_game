from GameEngine.globalEnv.enums import Actions, Directions
from bots_ai.field_handler.player_state import PlayerState


class DecisionMaker:
    def __init__(self, game_rules: dict, players: dict[str, PlayerState]):
        self.game_rules = game_rules
        self.players = players

    def make_decision(self, player_name: str) -> tuple[Actions, Directions | None]:
        """Среднее первое действие по всем настоящим листам игрока"""
        current_player = self.players.get(player_name)
        player_leaves = current_player.get_real_spawn_leaves()
        for leaf in player_leaves:
            gr = leaf.get_graph()

        first_actions = []

        return self.calc_avg_action(first_actions)

    def calc_avg_action(self, first_actions: list) -> tuple[Actions, Directions | None]:
        ...
