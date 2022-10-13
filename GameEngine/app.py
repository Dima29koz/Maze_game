"""runs game local for testing GameEngine"""
import random
from typing import Generator
import threading
import requests

from GUI.spectator import SpectatorGUI
from GameEngine.game import Game
from GameEngine.globalEnv.enums import Actions, Directions
from GameEngine.globalEnv.types import Position, LevelPosition
from GameEngine.rules import rules as ru

from bots_ai.core import BotAI
from bots_ai.field_handler.grid import Grid

from bots_ai.field_handler.test_graph import test_graph


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
        self.rules['generator_rules']['rows'] = 6
        self.rules['generator_rules']['cols'] = 6
        self.rules['generator_rules']['is_separated_armory'] = True
        # self.rules['generator_rules']['seed'] = random.random()
        self.rules['generator_rules']['seed'] = 2
        # self.rules['generator_rules']['levels_amount'] = 2
        self.rules['gameplay_rules']['fast_win'] = False
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
        self.bot = BotAI(self.rules, players_)
        self.bot.real_field = self.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field  # todo only for testing

    def run(self, auto=False):
        field = self.game.field
        gui = SpectatorGUI(field, self.bot)

        state = Actions.move
        is_running = True
        dis = Actions.move, Directions.top
        for _ in self.players:
            act = (Actions.info, None) if not self.is_replay else next(self.turns)
            is_running, dis = self.process_turn(*act)

        while is_running:
            act_pl_abilities = field.get_player_allowed_abilities(self.game.get_current_player())
            gui.draw(act_pl_abilities, self.game.get_current_player().name)
            act, state = gui.get_action(act_pl_abilities, state)
            if act:
                if auto:
                    act = dis
                else:
                    act = act if not self.is_replay else next(self.turns)
                is_running, dis = self.process_turn(*act)
        gui.close()
        # self.replay_file.close()

    def process_turn(self, action: Actions, direction: Directions):
        # if self.save_replay:
        #     self.replay_file.write(action.name + ',' + direction.name if direction else '' + '\n')
        response, next_player = self.game.make_turn(action.name, direction.name if direction else None)
        print(response.get_turn_info(), response.get_info())
        dis = None
        if self.bot:
            print(response.get_raw_info())
            self.bot.process_turn_resp(response.get_raw_info())
            self.bot.turn_prepare(self.game.get_current_player().name)
            dis = self.bot.make_decision(self.game.get_current_player().name)
            # print('avg', dis)
        if self.game.is_win_condition(self.rules):
            return False, ()
        return True, dis


def draw_graph(grid: Grid):
    gb = test_graph(grid)
    while True:
        try:
            p1 = Position(*[int(i) for i in input('p1: (x, y):').split(',')])
            p2 = Position(*[int(i) for i in input('p2: (x, y):').split(',')])
            gb.get_path(grid.get_cell(p1), grid.get_cell(p2))
        except Exception:
            print('stopped')
            break


def main(room_id: int = None, server_url: str = '', with_bot: bool = True):
    game = LocalGame(room_id, server_url, with_bot)
    start_map = Grid(game.game.field.game_map.get_level(LevelPosition(0, 0, 0)).field)
    game.run(auto=True)
    # tr1 = threading.Thread(target=game.run, kwargs={'auto': True})
    # tr2 = threading.Thread(target=draw_graph, args=(start_map,))
    # tr1.start()
    # tr2.start()

    # tr1.join()
    # tr2.join()


if __name__ == "__main__":
    r_id = 43
    s_url = '192.168.1.118:5000'
    # main(room_id=r_id, server_url=s_url, with_bot=True)
    main()
