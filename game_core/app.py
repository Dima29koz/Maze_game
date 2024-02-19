"""runs game local for testing game_engine"""
import random
import time
from typing import Generator
import requests

from game_core.game_engine import Game, base_rules as ru
from game_core.game_engine import Actions, Directions, Position, LevelPosition

from game_core.bots_ai.core import BotAI, BotAIDebug
from game_core.bots_ai.field_handler.grid import Grid
from game_core.bots_ai.decision_making.draw_graph_utils import test_graph


class LocalGame:
    def __init__(
            self, num_players=2, spawn_points: tuple = None, seed: float = None,
            room_id: int = None, server_url: str = '', with_bot=False, save_replay=True
    ):
        self.bot: BotAI | None = None
        self.is_replay = False
        self.turn_number = 0
        self.save_replay = save_replay
        self.players = []
        self.turns: list | Generator = []
        self.rules = {}
        if room_id is None or server_url == '':
            self.setup_game_local(num_players, spawn_points, seed)
        else:
            self.is_replay = True
            self.setup_game_replay(room_id, server_url)
        self.game = Game(rules=self.rules)
        field = self.game.field
        for i, player in enumerate(self.players, 1):
            field.spawn_player(*player, turn=i)
        if with_bot:
            self._init_bot()

    def setup_game_local(self, num_players: int, spawn_points: tuple | None, seed: float = None):
        self.rules = ru
        # self.rules['generator_rules']['river_rules']['has_river'] = False
        # self.rules['generator_rules']['walls']['has_walls'] = False
        # self.rules['generator_rules']['exits_amount'] = 20
        # self.rules['generator_rules']['rows'] = 6
        # self.rules['generator_rules']['cols'] = 6
        self.rules['generator_rules']['is_separated_armory'] = True
        self.rules['generator_rules']['seed'] = random.random() if seed is None else seed
        # self.rules['generator_rules']['levels_amount'] = 2
        self.rules['gameplay_rules']['fast_win'] = True
        self.rules['gameplay_rules']['diff_outer_concrete_walls'] = True
        # self.rules['generator_rules']['river_rules']['min_coverage'] = 90
        # self.rules['generator_rules']['river_rules']['max_coverage'] = 100

        self.players = self._create_players(num_players, spawn_points)
        self.turns = []

    def _create_players(self, num_players: int, spawn_points: tuple | None):
        random.seed(self.rules.get('generator_rules').get('seed'))
        if spawn_points and len(spawn_points) == num_players:
            return [(spawn_points[i], f'player_{i}') for i, spawn_point in enumerate(spawn_points)]
        return [(self._create_spawn(), f'player_{i}') for i in range(num_players)]

    def _create_spawn(self) -> dict[str, int]:
        return {
            'x': random.randint(1, self.rules.get('generator_rules').get('cols')),
            'y': random.randint(1, self.rules.get('generator_rules').get('rows'))
        }

    def setup_game_replay(self, room_id: int, server_url: str):
        resp = self._get_game_data(room_id, server_url)
        if not resp:
            return
        self.rules = resp.get('rules')
        self.turns = self._get_turn(resp.get('turns'))
        self.players = []
        for player in resp.get('spawn_points'):
            self.players.append((player.get('point'), player.get('name')))

    @staticmethod
    def _get_game_data(room_id: int, server_url: str) -> dict | None:
        try:
            response = requests.get(f'http://{server_url}/api/room_data/{room_id}')
            return response.json()
        except Exception as ex:
            print(ex)
            return

    @staticmethod
    def _get_turn(turns: list):
        for turn in turns:
            yield Actions[turn.get('action')], Directions[turn.get('direction')] if turn.get('direction') else None

    def _init_bot(self):
        players_: dict[str, Position] = {
            player_name: Position(pl_pos.get('x'), pl_pos.get('y')) for pl_pos, player_name in self.players}
        self.bot = BotAIDebug(self.rules, players_)
        self.bot.real_field = self.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field  # todo only for testing

    def run(self, auto=False, skip_turns=0):
        print('seed:', self.rules['generator_rules']['seed'])
        field = self.game.field

        from game_core.GUI import SpectatorGUI
        gui = SpectatorGUI(field, self.bot)

        state = Actions.move
        is_running = True
        for _ in self.players:
            act = (Actions.info, None) if not self.is_replay else next(self.turns)
            is_running, _ = self.process_turn(*act)

        while is_running:
            act_pl_abilities = self.game.get_allowed_abilities(self.game.get_current_player())
            act, state = gui.get_action(act_pl_abilities, state)
            action = None
            if act or self.turn_number < skip_turns:
                if auto:
                    action = self.bot.make_decision(self.game.get_current_player().name, act_pl_abilities)
                else:
                    action = act if not self.is_replay else next(self.turns)
            gui.draw(act_pl_abilities, self.game.get_current_player().name)
            if action:
                is_running, _ = self.process_turn(*action)
        gui.close()

    def run_performance_test(self, verbose=False):
        print('seed:', self.rules['generator_rules']['seed'])

        is_running = True
        for _ in self.players:
            act = (Actions.info, None) if not self.is_replay else next(self.turns)
            is_running, _ = self.process_turn(*act, verbose=verbose)
        step = 0
        times = []
        tr_step = 0
        num_shot = 0
        shot_success = 0
        leaves = {player: [] for player in self.bot.players.keys()}
        while is_running:
            current_player = self.game.get_current_player()
            act_pl_abilities = self.game.get_allowed_abilities(current_player)

            time_start = time.time()
            act = self.bot.make_decision(current_player.name, act_pl_abilities)
            is_running, response = self.process_turn(*act, verbose=verbose)
            time_end = time.time() - time_start

            if tr_step == 0 and act[0] is Actions.swap_treasure:
                tr_step = step
            if act[0] is Actions.shoot_bow:
                num_shot += 1
            [leaves[player].append(len(state.get_leaf_nodes())) for player, state in self.bot.players.items()]
            if response.get_raw_info().get('response').get('hit'):
                shot_success += 1
            times.append(time_end)
            step += 1
        return times, step, tr_step, num_shot, shot_success, leaves

    def process_turn(self, action: Actions, direction: Directions, verbose=True):
        response, next_player = self.game.make_turn(action.name, direction.name if direction else None)
        if verbose:
            print(self.turn_number, response.get_turn_info(), response.get_info())
        if self.bot:
            self.bot.process_turn_resp(response.get_raw_info())
        self.turn_number += 1
        if self.game.is_win_condition(self.rules):
            return False, response
        return True, response


def draw_graph(grid: Grid, player_cell=None, player_abilities=None):
    test_graph(grid, player_cell, player_abilities)


def main(
        num_players: int = 2, spawn_points: tuple = None, seed: float = None,
        room_id: int = None, server_url: str = '', with_bot: bool = True, show_graph=False, skip_turns=0
):
    game = LocalGame(num_players, spawn_points, seed, room_id, server_url, with_bot)
    start_map = Grid(game.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field)
    current_player = game.game.get_current_player()
    current_player_abilities = game.game.get_allowed_abilities(current_player)
    if show_graph:
        draw_graph(start_map, current_player.cell, current_player_abilities)
    game.run(auto=True, skip_turns=skip_turns)


if __name__ == "__main__":
    _seed = 0.5380936623177652
    # _seed = 0.18378379396666744  # slow
    # _seed = 0.41856783943105225  # too slow
    # _seed = random.random()
    _num_players = 4
    _spawn_points = (
        {'x': 5, 'y': 3},
        {'x': 2, 'y': 4},
        {'x': 2, 'y': 1},
        {'x': 3, 'y': 2},
    )
    main(num_players=_num_players, spawn_points=None, seed=_seed, skip_turns=1000)
    # main(num_players=_num_players, spawn_points=_spawn_points[:_num_players], seed=_seed)
