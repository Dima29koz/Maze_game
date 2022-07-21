"""runs game local for testing GameEngine"""
import random

from GUI.spectator import SpectatorGUI
from GameEngine.game import Game
from GameEngine.globalEnv.enums import Actions

from GameEngine.rules import rules
from bots_ai.turn_state import BotAI


def main():
    # rules['generator_rules']['river_rules']['has_river'] = False
    # rules['generator_rules']['walls']['has_walls'] = False
    rules['generator_rules']['exits_amount'] = 20
    rules['gameplay_rules']['fast_win'] = False
    rules['generator_rules']['river_rules']['min_coverage'] = 90
    rules['generator_rules']['river_rules']['max_coverage'] = 100
    spawn = {'x': 3, 'y': 1}
    bot = None

    random.seed(5)
    game = Game(rules=rules)
    field = game.field
    field.spawn_player(spawn, 'Skipper', 1)
    # field.spawn_player({'x': 1, 'y': 1}, 'Tester', 2)

    bot = BotAI(rules, 'Skipper', pos_x=3, pos_y=1)
    # bot = BotAI(rules, 'Skipper', pos_x=2, pos_y=0)
    gui = SpectatorGUI(field, bot)

    state = Actions.move
    is_running = True

    response = game.field.action_handler(Actions.info)
    print(response.get_turn_info(), response.get_info())
    # print(response.get_raw_info().get('response'))
    bot.process_turn_resp(response.get_raw_info())

    while is_running:
        act_pl_abilities = field.get_player_allowed_abilities(game.get_current_player())
        gui.draw(act_pl_abilities)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:
            response = game.field.action_handler(*act)
            print(response.get_turn_info(), response.get_info())
            # print(response.get_raw_info().get('response'))
            bot.process_turn_resp(response.get_raw_info())
            print('Has real - ', bot.has_real_field(field.field))
            if game.is_win_condition(rules):
                is_running = False

    gui.close()


if __name__ == "__main__":
    main()
