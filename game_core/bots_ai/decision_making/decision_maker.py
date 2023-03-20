from random import choice

from ...game_engine.global_env.enums import Actions, Directions
from .graph_builder import GraphBuilder
from .target_calculator import TargetCalculator
from ..field_handler.player_state import PlayerState
from ..field_handler.player_stats import PlayerStats
from ..field_handler.tree_node import Node


class DecisionMaker:
    def __init__(self, game_rules: dict, players: dict[str, PlayerState]):
        self.game_rules = game_rules
        self.players = players
        self.players_stats: dict[str, PlayerStats] = {name: player.stats for name, player in self.players.items()}
        self.target_calculators: dict[str, TargetCalculator] = {
            name: TargetCalculator(name, self.players_stats.copy())
            for name, stats in self.players_stats.items()}

    def make_decision(self, player_name: str,
                      player_abilities: dict[Actions, bool]) -> tuple[Actions, Directions | None]:
        """Среднее первое действие по всем настоящим листам игрока"""
        current_player = self.players.get(player_name)
        if player_abilities.get(Actions.swap_treasure) and not current_player.stats.has_treasure:
            return Actions.swap_treasure, None

        player_leaves = current_player.get_real_spawn_leaves()
        first_actions: dict[tuple[Actions, Directions | None], int] = {}
        for leaf in player_leaves:
            act = self._calculate_first_action(leaf, player_name, player_abilities)
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

    def _calculate_first_action(self, leaf: Node, player_name: str, player_abilities: dict[Actions, bool]):
        if player_abilities.get(Actions.shoot_bow):
            shoot_direction = self._direction_to_shoot(leaf, player_name)
            if shoot_direction:
                return Actions.shoot_bow, shoot_direction
        graph = GraphBuilder(leaf.field_state.field, leaf.field_state.get_player_cell(player_name), player_abilities)
        target_calc = self.target_calculators.get(player_name)
        target_cell = target_calc.get_target(graph, leaf.field_state)
        return graph.get_first_act(target_cell)

    def _direction_to_shoot(self, leaf: Node, current_player_name: str) -> Directions | None:
        cur_pl_pos = leaf.field_state.get_player_pos(current_player_name)
        other_pl_pos = [
            pos for name, pos in leaf.field_state.players_positions.items()
            if name != current_player_name and pos and self.players_stats.get(name).is_alive]

        grid = leaf.field_state.field
        allowed_directions = []
        for direction in Directions:
            start_position = cur_pl_pos
            while start_position not in other_pl_pos:
                if grid.get_cell(start_position).walls[direction].weapon_collision:
                    break
                start_position = grid.get_neighbour_cell(start_position, direction).position
            else:
                allowed_directions.append(direction)
        if not allowed_directions:
            return
        return choice(allowed_directions)
