"""runs game local for testing game_engine"""
import random
import threading
from typing import Generator
import requests

from game_core.GUI import SpectatorGUI
from game_core.game_engine import Game, base_rules as ru
from game_core.game_engine import Actions, Directions, Position, LevelPosition

from game_core.bots_ai.core import BotAI, BotAIDebug
from game_core.bots_ai.field_handler.grid import Grid
from game_core.bots_ai.decision_making.draw_graph_utils import test_graph


class LocalGame:
    def __init__(self, room_id: int = None, server_url: str = '', with_bot=False, save_replay=True):
        self.bot: BotAI | None = None
        self.is_replay = False
        self.save_replay = save_replay
        # self.replay_file = open('replay.txt', 'w')
        self.players = []
        self.turns: list | Generator = []
        self.rules = {}
        if room_id is None or server_url == '':
            self.setup_game_local()
        else:
            self.is_replay = True
            self.setup_game_replay(room_id, server_url)
        self.game = Game(rules=self.rules)
        field = self.game.field
        for i, player in enumerate(self.players, 1):
            field.spawn_player(*player, turn=i)
        if with_bot:
            self._init_bot()

    def setup_game_local(self):
        self.rules = ru
        # self.rules['generator_rules']['river_rules']['has_river'] = False
        # self.rules['generator_rules']['walls']['has_walls'] = False
        # self.rules['generator_rules']['exits_amount'] = 20
        # self.rules['generator_rules']['rows'] = 6
        # self.rules['generator_rules']['cols'] = 6
        self.rules['generator_rules']['is_separated_armory'] = True
        # self.rules['generator_rules']['seed'] = random.random()
        self.rules['generator_rules']['seed'] = 0.18346507016243863
        # self.rules['generator_rules']['levels_amount'] = 2
        self.rules['gameplay_rules']['fast_win'] = True
        self.rules['gameplay_rules']['diff_outer_concrete_walls'] = True
        # self.rules['generator_rules']['river_rules']['min_coverage'] = 90
        # self.rules['generator_rules']['river_rules']['max_coverage'] = 100
        spawn: dict[str, int] = {'x': 5, 'y': 3}
        spawn2: dict[str, int] = {'x': 2, 'y': 4}
        spawn3: dict[str, int] = {'x': 2, 'y': 1}

        self.players = [
            (spawn, 'Skipper'),
            (spawn2, 'Tester'),
            # (spawn3, 'player'),
        ]
        self.turns = []

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
        self.bot = BotAIDebug(self.rules, players_, self.game.get_last_player_name())
        self.bot.real_field = self.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field  # todo only for testing

    def run(self, auto=False):
        print('seed:', self.rules['generator_rules']['seed'])
        field = self.game.field
        gui = SpectatorGUI(field, self.bot)

        state = Actions.move
        is_running = True
        for _ in self.players:
            act = (Actions.info, None) if not self.is_replay else next(self.turns)
            is_running = self.process_turn(*act)

        while is_running:
            act_pl_abilities = self.game.get_allowed_abilities(self.game.get_current_player())
            gui.draw(act_pl_abilities, self.game.get_current_player().name)
            act, state = gui.get_action(act_pl_abilities, state)
            if act:
                if auto:
                    act = self.bot.make_decision(self.game.get_current_player().name, act_pl_abilities)
                else:
                    act = act if not self.is_replay else next(self.turns)
                is_running = self.process_turn(*act)
        gui.close()
        # self.replay_file.close()

    def process_turn(self, action: Actions, direction: Directions):
        # if self.save_replay:
        #     self.replay_file.write(action.name + ',' + direction.name if direction else '' + '\n')
        response, next_player = self.game.make_turn(action.name, direction.name if direction else None)
        print(response.get_turn_info(), response.get_info())
        if self.bot:
            # print(response.get_raw_info())
            self.bot.process_turn_resp(response.get_raw_info())
            self.bot.turn_prepare(self.game.get_current_player().name)
        if self.game.is_win_condition(self.rules):
            return False
        return True


def draw_graph(grid: Grid, player_cell=None, player_abilities=None):
    gb = test_graph(grid, player_cell, player_abilities)
    # while True:
    #     try:
    #         p1 = Position(*[int(i) for i in input('p1: (x, y):').split(',')])
    #         p2 = Position(*[int(i) for i in input('p2: (x, y):').split(',')])
    #         gb.get_path(grid.get_cell(p1), grid.get_cell(p2))
    #     except Exception:
    #         print('stopped')
    #         break


def main(room_id: int = None, server_url: str = '', with_bot: bool = True):
    game = LocalGame(room_id, server_url, with_bot)
    start_map = Grid(game.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field)
    current_player = game.game.get_current_player()
    current_player_abilities = game.game.get_allowed_abilities(current_player)
    # game.run(auto=True)
    tr1 = threading.Thread(target=game.run, kwargs={'auto': True})
    tr2 = threading.Thread(target=draw_graph, args=(start_map, current_player.cell, current_player_abilities))
    tr1.start()
    tr2.start()

    tr1.join()
    tr2.join()


if __name__ == "__main__":
    r_id = 43
    s_url = '192.168.1.118:5000'
    # main(room_id=r_id, server_url=s_url, with_bot=True)
    main()
