"""runs game local for testing GameEngine"""
import random

import requests

from GUI.spectator import SpectatorGUI
from GameEngine.game import Game
from GameEngine.globalEnv.enums import Actions, Directions

from GameEngine.rules import rules as ru
from bots_ai.core import BotAI


def get_game_data(room_id: int) -> dict:
    response = requests.get(f'http://192.168.1.118:5000/api/room_data/{room_id}')
    return response.json()


def get_turn(turns: list[dict]):
    for turn in turns:
        yield Actions[turn.get('action')], Directions[turn.get('direction')] if turn.get('direction') else None


def process_turn(game, bot, action, direction, rules):
    response = game.field.action_handler(action, direction)
    print(response.get_turn_info(), response.get_info())
    player_name = response.get_turn_info().get('player_name')
    # print(response.get_raw_info().get('response'))
    bot.process_turn_resp(response.get_raw_info())
    print('spawns: ', bot.get_spawn_amount(player_name))
    # print('Has bad nodes - ', bot.has_bad_nodes(player_name))

    bot.turn_prepare(game.get_current_player().name)
    if game.is_win_condition(rules):
        return False
    return True


def setup_game_local():
    rules = ru
    # rules['generator_rules']['river_rules']['has_river'] = False
    # rules['generator_rules']['walls']['has_walls'] = False
    # rules['generator_rules']['exits_amount'] = 20
    rules['generator_rules']['is_separated_armory'] = True
    # rules['generator_rules']['seed'] = random.random()
    rules['generator_rules']['seed'] = 5
    rules['gameplay_rules']['fast_win'] = False
    rules['gameplay_rules']['diff_outer_concrete_walls'] = True
    # rules['generator_rules']['river_rules']['min_coverage'] = 90
    # rules['generator_rules']['river_rules']['max_coverage'] = 100
    spawn: dict[str, int] = {'x': 1, 'y': 1}
    spawn2: dict[str, int] = {'x': 2, 'y': 3}

    players = [
        (spawn, 'Skipper'),
        (spawn2, 'Tester'),
    ]
    return rules, players


def main(room_id: int = None):
    if room_id is None:
        rules, players = setup_game_local()
        turns = []
    else:
        resp = get_game_data(room_id)
        rules = resp.get('rules')
        turns = get_turn(resp.get('turns'))
        players = []
        for player in resp.get('spawn_points'):
            players.append((player.get('point'), player.get('name')))

    game = Game(rules=rules)
    field = game.field
    for i, player in enumerate(players, 1):
        field.spawn_player(*player, turn=i)

    bot = BotAI(rules, players)
    bot.real_field = field.field
    gui = SpectatorGUI(field, bot)

    state = Actions.move
    is_running = True

    for _ in players:
        act = (Actions.info, None) if room_id is None else next(turns)
        response = game.field.action_handler(*act)
        print(response.get_turn_info(), response.get_info())
        bot.process_turn_resp(response.get_raw_info())
        bot.turn_prepare(game.get_current_player().name)

    while is_running:
        act_pl_abilities = field.get_player_allowed_abilities(game.get_current_player())
        gui.draw(act_pl_abilities, game.get_current_player().name)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:
            act = act if room_id is None else next(turns)
            is_running = process_turn(game, bot, *act, rules=rules)
    gui.close()


if __name__ == "__main__":
    # ids: 42
    main(room_id=43)
